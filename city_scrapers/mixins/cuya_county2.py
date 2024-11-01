import re
from datetime import datetime, time

import dateutil.parser
from city_scrapers_core.items import Meeting


class CuyaCountyMixin2:
    """This is a newer version of CuyaCountyMixin that handles page structure
    changes to the Cuyahoga County site that occured in 2023. It is not yet
    used in all spiders. When it is, the old mixin can be removed and this
    one renamed to CuyaCountyMixin."""

    timezone = "America/Detroit"

    # CSS selectors defined as class constants for reuse and maintainability
    LINK_SELECTOR = (
        ".row.bceventgrid > table > tbody > tr > td:nth-child(2) > a::attr(href)"
    )
    TITLE_SELECTOR = "h1.title::text"
    DESCRIPTION_SELECTOR = ".content ::text"

    def parse(self, response):
        """Extract and follow meeting detail links."""
        for href in response.css(self.LINK_SELECTOR).extract():
            yield response.follow(
                href,
                callback=self._parse_detail,
                dont_filter=True,
            )

    def _parse_detail(self, response):
        """Parse meeting details and create Meeting object."""
        main_el = response.css("div.moudle")
        start_date, end_date = self._parse_dates(main_el)

        # Create meeting object with all parsed data
        meeting = Meeting(
            title=main_el.css(self.TITLE_SELECTOR).get("").strip(),
            description=self._parse_description(main_el),
            classification=self.classification,
            start=start_date,
            end=end_date,
            time_notes="",
            all_day=False,
            location=self._parse_location(main_el),
            links=self._parse_links(main_el),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_description(self, selector):
        """Extract and clean meeting description text from the HTML.

        Args:
            selector: A Scrapy selector pointing to the main content area

        Returns:
            str: A cleaned description string with:
                - All text fragments extracted from content area
                - Whitespace trimmed from each fragment
                - Empty fragments removed
                - Remaining fragments joined with spaces

        Example:
            Input HTML: <div class="content">
                         <p>Meeting to discuss</p>
                         <p>  budget items  </p>
                         <p></p>
                       </div>
            Output: "Meeting to discuss budget items"
        """
        # Extract all text fragments from the content area
        raw_texts = selector.css(self.DESCRIPTION_SELECTOR).extract()

        # Clean each text fragment and filter out empty ones
        cleaned_texts = [
            text.strip() for text in raw_texts if text.strip()  # Remove empty fragments
        ]

        # Join the cleaned fragments with spaces
        return " ".join(cleaned_texts)

    # Compile regex patterns at class level for better performance
    TIME_PATTERN = re.compile(r"\b([1-9]|1[0-2]):[0-5][0-9]\s*(AM|PM)\b", re.IGNORECASE)
    DEFAULT_TIME = time(0, 0)

    def _parse_dates(self, selector):
        """Extract start and end dates from the page.

        Returns tuple of datetime objects.
        Defaults to 12:00 AM start and None end if parsing fails.
        """
        # Get start date
        start_date_str = selector.css('.meta-item[itemprop="startDate"] ::attr(content)').get()
        if not start_date_str:
            raise ValueError("Could not find start date")
        start_date = dateutil.parser.parse(start_date_str).date()
        
        # Get start time
        text_nodes = selector.css(".meta-item[itemprop='startDate'] > p::text").extract()
        if len(text_nodes) < 2 or not (start_time_str := text_nodes[1].strip()):
            return datetime.combine(start_date, self.DEFAULT_TIME), None
            
        try:
            start_time = dateutil.parser.parse(start_time_str).time()
        except (ValueError, TypeError):
            return datetime.combine(start_date, self.DEFAULT_TIME), None
            
        # Get end time
        time_text = " ".join(selector.css(".meta-item p ::text").extract()).strip()
        if " - " not in time_text:
            return datetime.combine(start_date, start_time), None
            
        end_time_str = time_text.split(" - ")[1].strip()
        if match := self.TIME_PATTERN.search(end_time_str):
            try:
                end_time = dateutil.parser.parse(match.group()).time()
                return (
                    datetime.combine(start_date, start_time),
                    datetime.combine(start_date, end_time)
                )
            except (ValueError, TypeError):
                pass
                
        return datetime.combine(start_date, start_time), None

        # combine
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(start_date, end_time)
        return start_datetime, end_datetime

    # Additional CSS selectors
    LOCATION_SELECTOR = 'div[itemprop="location"] [itemprop="streetAddress"]::text'
    LINKS_SELECTOR = ".related-content a"
    
    def _parse_location(self, response):
        """Extract meeting location information from the HTML.

        Args:
            selector: A Scrapy selector pointing to the main content area

        Returns:
            dict: A location dictionary containing:
                - name: Currently empty as location names are not provided
                - address: The street address of the meeting location, cleaned of whitespace

        Example:
            Input HTML: <div itemprop="location">
                         <span itemprop="streetAddress">
                           2079 East 9th St Cleveland, OH 44115
                         </span>
                       </div>
            Output: {
                "name": "",
                "address": "2079 East 9th St Cleveland, OH 44115"
            }

        Note:
            If no address is found, returns empty string as address
        """
        # Extract and clean the address from the location element
        raw_address = selector.css(self.LOCATION_SELECTOR).get("")
        clean_address = raw_address.strip()

        return {
            "name": "",  # Location name not provided in current HTML structure
            "address": clean_address,
        }

    def _parse_links(self, selector):
        """Extract meeting-related links and their titles from the HTML.

        Args:
            selector: A Scrapy selector pointing to the main content area

        Returns:
            list: A list of dictionaries, each containing:
                - title: The display text of the link, cleaned of whitespace
                - href: The URL that the link points to

        Example:
            Input HTML: <div class="related-content">
                         <a href="http://example.com/agenda.pdf">
                           <span>Meeting Agenda</span>
                         </a>
                         <a href="http://example.com/minutes.pdf">
                           <span>Meeting Minutes</span>
                         </a>
                       </div>
            Output: [
                {
                    "title": "Meeting Agenda",
                    "href": "http://example.com/agenda.pdf"
                },
                {
                    "title": "Meeting Minutes",
                    "href": "http://example.com/minutes.pdf"
                }
            ]
        """
        # Find all link elements in the related content section
        link_elements = selector.css(self.LINKS_SELECTOR)

        # Extract and clean the title and href for each link
        meeting_links = []
        for link in link_elements:
            link_data = {
                "title": link.css("span::text").get("").strip(),
                "href": link.css("::attr(href)").get(""),
            }
            meeting_links.append(link_data)

        return meeting_links
