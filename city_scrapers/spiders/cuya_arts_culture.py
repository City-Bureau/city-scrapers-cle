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

    def parse(self, response):
        """
        First we parse the board materials page, creating a dictionary of
        links to meeting materials indexed by meeting dates. Then we
        scrape the the meeting schedule page itself.
        """
        links_dict = {}
        material_els = response.css(".accordion-body p")
        for item in material_els:
            meeting_date_str = item.css("strong::text").extract_first()
            if not meeting_date_str:
                continue
            # regex to extract meeting date in format "Month DD, YYYY"
            meeting_date_regex = re.search(
                r"[A-Z][a-z]+ \d{1,2}, \d{4}", meeting_date_str
            )
            if not meeting_date_regex:
                continue
            meeting_date_str = meeting_date_regex.group()
            meeting_date = dateparse(meeting_date_str)
            link_els = item.css("a")
            if not link_els:
                continue
            links = []
            for link_el in link_els:
                title = link_el.css("::text").extract_first()
                if not title:
                    # hidden link, skip
                    continue
                relative_href = link_el.css("::attr(href)").extract_first()
                abs_hrf = response.urljoin(relative_href)
                links.append({"title": title, "href": abs_hrf})
            links_dict[meeting_date] = links

        # now scrape meeting agenda page
        yield response.follow(
            "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/",
            self._parse_schedule,
            meta={"links_dict": links_dict},
        )

    def _parse_schedule(self, response):
        """
        Parse the meeting schedule page and merge meeting materials
        with meeting schedule based on meeting date.
        """
        links_dict = response.meta["links_dict"]
        schedule_els = response.css(".grid-section .row .column p")
        for schedule_el in schedule_els:
            text_chunks = schedule_el.css("::text").extract()
            clean_chunks = [re.sub(r"\s+", " ", chunk.strip()) for chunk in text_chunks]
            meeting_title = clean_chunks[0]
            meeting_datetime_str = clean_chunks[1]
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

    def _parse_meeting_date(self, meeting_datetime_str):
        """
        Extract meeting date from a string in the format "Month DD, YYYY".
        """
        meeting_date_regex = re.search(
            r"[A-Z][a-z]+ \d{1,2}, \d{4}", meeting_datetime_str
        )
        if not meeting_date_regex:
            return None
        meeting_date_str = meeting_date_regex.group()
        meeting_date = dateparse(meeting_date_str)
        return meeting_date

    def _parse_meeting_time(self, meeting_datetime_str):
        """
        Extract meeting time from a string in the format
        "at 8:30 a.m." or "at 4 p.m." etc
        """
        meeting_time_regex = re.search(
            r"at (\d{1,2}(:\d{2})? [ap]\.m\.)", meeting_datetime_str
        )
        if not meeting_time_regex:
            return None
        meeting_time_str = meeting_time_regex.group(1)
        datetime_obj = dateparse(meeting_time_str)
        # just return time
        return datetime_obj.time()

    def _parse_location(self, text_chunks):
        """
        Extract location from a list of text chunks.
        Assume everything between the 3rd and finals
        chunks is location information.
        """
        default = {"name": "", "address": "TBD"}
        if len(text_chunks) < 4:
            return default
        # use regex to find address chunk in format "OH 44101" or
        location_chunks = text_chunks[2:]
        address_pattern = re.compile(r"[A-Z]{2} \d{5}")
        for chunk in location_chunks:
            if address_pattern.search(chunk):
                self.logger.info(f"Found address: {chunk}")
                name = ""
                # if address is the last chunk, assume preceding chunks are
                # the location name
                if chunk == location_chunks[-1]:
                    name = " ".join(location_chunks[:-1])
                    # remove excess whitespace
                    name = re.sub(r"\s+", " ", name)
                    # remove any chars that are not letters, numbers, spaces, hyphens
                    name = re.sub(r"[^a-zA-Z0-9\s-]", "", name)
                return {"name": name, "address": chunk}
        return default
