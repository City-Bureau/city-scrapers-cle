import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse as dateparse


class CuyaArtsCultureSpider(CityScrapersSpider):
    name = "cuya_arts_culture"
    agency = "Cuyahoga County Arts & Culture"
    timezone = "America/Detroit"
    start_urls = ["https://www.cacgrants.org/about-us/meet-our-board/board-materials/"]

    # Compile regex patterns once at class level for better performance
    DATE_PATTERN = re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}")
    
    def parse(self, response):
        """Parse board materials page to create a dictionary of meeting materials links,
        then scrape the meeting schedule page."""
        links_dict = {}
        for item in response.css(".accordion-body p"):
            meeting_date = self._extract_meeting_date(item)
            if not meeting_date:
                continue

            links = self._extract_links(item, response)
            if links:
                links_dict[meeting_date] = links

        # Scrape meeting agenda page
        yield response.follow(
            "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/",
            self._parse_schedule,
            meta={"links_dict": links_dict},
        )

    def _parse_schedule(self, response):
        """Parse the meeting schedule page and merge meeting materials
        with schedule based on meeting date."""
        links_dict = response.meta["links_dict"]
        schedule_els = response.css(".grid-section .row .column p")
        
        for schedule_el in schedule_els:
            # Extract and clean text chunks
            text_chunks = schedule_el.css("::text").extract()
            clean_chunks = [re.sub(r"\s+", " ", chunk.strip()) for chunk in text_chunks]
            
            # Parse meeting details
            meeting_title = clean_chunks[0]
            meeting_datetime_str = clean_chunks[1]
            
            # Parse date and time
            meeting_date = self._parse_meeting_date(meeting_datetime_str)
            if not meeting_date:
                self.logger.warning(
                    f"Could not parse meeting date: {meeting_datetime_str}"
                )
                continue
                
            meeting_time = self._parse_meeting_time(meeting_datetime_str)
            if not meeting_time:
                self.logger.warning(
                    f"Could not parse meeting time: {meeting_datetime_str}"
                )
                continue
                
            # Create meeting object
            start = datetime.combine(meeting_date, meeting_time)
            meeting_links = links_dict.get(meeting_date, [])
            
            meeting = Meeting(
                title=meeting_title,
                description="",
                classification=BOARD,
                start=start,
                end=None,
                time_notes="",
                all_day=False,
                location=self._parse_location(clean_chunks),
                links=meeting_links,
                source=response.url,
            )
            
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _extract_meeting_date(self, item):
        """Extract and parse meeting date from item.

        Args:
            item: Scrapy selector for meeting item

        Returns:
            datetime.date or None: Parsed meeting date if found
        """
        meeting_date_str = item.css("strong::text").extract_first()
        if not meeting_date_str:
            return None

        match = self.DATE_PATTERN.search(meeting_date_str)
        return dateparse(match.group()) if match else None

    def _extract_links(self, item, response):
        """Extract and format links from item.

        Args:
            item: Scrapy selector for meeting item
            response: Scrapy response object for resolving relative URLs

        Returns:
            list: List of dicts with title and href for each link
        """
        links = []
        for link_el in item.css("a"):
            title = link_el.css("::text").extract_first()
            if not title:  # Skip hidden links
                continue
            href = response.urljoin(link_el.css("::attr(href)").extract_first())
            links.append({"title": title, "href": href})
        return links

    # Compile time pattern once
    TIME_PATTERN = re.compile(r"at (\d{1,2}(:\d{2})? [ap]\.m\.)")
    
    def _parse_meeting_date(self, meeting_datetime_str):
        """Extract meeting date using compiled pattern.

        Args:
            meeting_datetime_str: String containing date information

        Returns:
            datetime.date or None: Parsed meeting date if found
        """
        match = self.DATE_PATTERN.search(meeting_datetime_str)
        return dateparse(match.group()) if match else None

    def _parse_meeting_time(self, meeting_datetime_str):
        """Extract meeting time using compiled pattern.

        Args:
            meeting_datetime_str: String containing time information

        Returns:
            datetime.time or None: Parsed meeting time if found
        """
        match = self.TIME_PATTERN.search(meeting_datetime_str)
        if not match:
            return None
        return dateparse(match.group(1)).time()

    # Compile address and cleanup patterns
    ADDRESS_PATTERN = re.compile(r"[A-Z]{2} \d{5}")
    CLEANUP_PATTERN = re.compile(r"[^a-zA-Z0-9\s-]")
    
    def _parse_location(self, text_chunks):
        """Extract location information from text chunks.

        Args:
            text_chunks: List of text strings containing location information

        Returns:
            dict: Location dictionary with name and address fields
        """
        default = {"name": "", "address": "TBD"}
        if len(text_chunks) < 4:
            return default
            
        location_chunks = text_chunks[2:]
        for i, chunk in enumerate(location_chunks):
            if self.ADDRESS_PATTERN.search(chunk):
                if chunk == location_chunks[-1]:
                    name = " ".join(location_chunks[:i])
                    name = re.sub(r"\s+", " ", name.strip())
                    name = self.CLEANUP_PATTERN.sub("", name)
                    return {"name": name, "address": chunk}
                return {"name": "", "address": chunk}
        return default
