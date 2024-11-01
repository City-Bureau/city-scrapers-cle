import re
from datetime import datetime

from city_scrapers_core.items import Meeting


class CuyaCountyMixin:
    """
    Mixin for scraping meeting information from Cuyahoga County websites.
    Provides common parsing methods for meeting details across different departments.
    """
    timezone = "America/Detroit"
    location = {
        "name": "County Headquarters",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    # CSS selectors defined as class constants for reuse
    DETAIL_LINK_SELECTOR = ".gridViewStyle td:nth-child(2) a::attr(href)"
    TITLE_SELECTOR = "#contentColumn h1::text"
    DATETIME_SELECTOR = "blockquote dd::text"

    # Date/time format constants
    DATETIME_FORMAT = "%m/%d/%Y-%I:%M %p"
    
    def parse(self, response):
        """Parse the list page to find and follow links to individual meeting pages.

        Args:
            response: Scrapy response object from the list page

        Yields:
            Scrapy Request objects for each meeting detail page
        """
        for detail_link in response.css(self.DETAIL_LINK_SELECTOR).extract():
            yield response.follow(
                detail_link,
                callback=self._parse_detail,
                dont_filter=True
            )

    def _parse_detail(self, response):
        """
        Parse an individual meeting page to create a Meeting object.
        
        Args:
            response: Scrapy response object from a meeting detail page
            
        Yields:
            Meeting: Object containing all parsed meeting information
        """
        title = self._parse_title(response)
        start, end = self._parse_start_end(response)
        
        meeting = Meeting(
            title=title,
            description=self._parse_description(response),
            classification=self._parse_classification(title),
            start=start,
            end=end,
            time_notes="",
            all_day=False,
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,  # Direct use instead of separate method
        )
        
        meeting["status"] = self._get_status(meeting)  # Direct use instead of _parse_status
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, response):
        """
        Extract and clean the meeting title.
        
        Args:
            response: Scrapy response object
            
        Returns:
            str: Cleaned meeting title with " Meeting" removed unless it's a special meeting
        """
        title_str = response.css(self.TITLE_SELECTOR).extract_first().strip()
        if "Special" in title_str:
            return title_str
        return title_str.replace(" Meeting", "").strip()

    def _parse_start_end(self, response):
        """Extract start and end times for the meeting.

        Args:
            response: Scrapy response object

        Returns:
            tuple: (start datetime, end datetime or None)

        Note:
            End time might be None if not provided or if parsing fails
        """
        datetime_strings = [
            d.strip() for d in response.css(self.DATETIME_SELECTOR).extract()
        ]

        if not datetime_strings:
            raise ValueError("No datetime information found")

        # Parse start time (required)
        start = datetime.strptime(datetime_strings[0], self.DATETIME_FORMAT)

        # Parse end time (optional)
        end = None
        if len(datetime_strings) > 1:
            try:
                end = datetime.strptime(datetime_strings[1], self.DATETIME_FORMAT)
            except ValueError:
                # End time parsing failed, leave as None
                pass

        return start, end

    # Additional CSS selectors
    LINKS_SELECTOR = "blockquote a"
    VIDEO_SELECTOR = ".embed-container iframe"
    
    # Regex patterns for location parsing
    ROOM_NUMBER_PATTERN = re.compile(r" \d{3}")
    WHITESPACE_PATTERN = re.compile(r"\s+")

    def _parse_description(self, response):
        """
        Parse meeting description (currently returns empty string as descriptions
        are not provided in the source HTML).
        
        Args:
            response: Scrapy response object
            
        Returns:
            str: Empty string as descriptions are not available
        """
        return ""

    def _parse_classification(self, title):
        """
        Get meeting classification (uses classification defined in spider).
        
        Args:
            title: Meeting title string (unused in base implementation)
            
        Returns:
            str: Classification string defined in spider class
        """
        return self.classification

    def _parse_location(self, response):
        """
        Extract meeting location from detail strings.
        
        Args:
            response: Scrapy response object
            
        Returns:
            str or None: Location string containing room number if found,
                        None if no valid location found
                        
        Example:
            Input: "Room 123 County Building"
            Output: "Room 123 County Building"
        """
        detail_strings = response.css(self.DATETIME_SELECTOR).extract()
        
        # Look for strings containing room numbers (e.g., " 123")
        for detail_str in detail_strings:
            if self.ROOM_NUMBER_PATTERN.search(detail_str):
                # Clean up whitespace and return
                return self.WHITESPACE_PATTERN.sub(" ", detail_str).strip()
                
        return None

    def _parse_links(self, response):
        """
        Extract links to meeting materials and video streams.
        
        Args:
            response: Scrapy response object
            
        Returns:
            list: List of dictionaries containing:
                - title: Link text or "Video" for video streams
                - href: Absolute URL to resource
                
        Example:
            [
                {"title": "Agenda PDF", "href": "http://example.com/agenda.pdf"},
                {"title": "Video", "href": "http://example.com/stream"}
            ]
        """
        links = []
        
        # Parse document links
        for link in response.css(self.LINKS_SELECTOR):
            links.append({
                "title": " ".join(link.css("*::text").extract()),
                "href": response.urljoin(link.attrib["href"])
            })
            
        # Parse video streams
        for iframe in response.css(self.VIDEO_SELECTOR):
            links.append({
                "title": "Video",
                "href": iframe.attrib["src"]
            })
            
        return links
