import re

import scrapy
from city_scrapers_core.constants import (
    ADVISORY_COMMITTEE,
    BOARD,
    COMMITTEE,
    NOT_CLASSIFIED,
)
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse
from scrapy_playwright.page import PageMethod


class CleTransitSpider(CityScrapersSpider):
    name = "cle_transit"
    agency = "Greater Cleveland Regional Transit Authority"
    timezone = "America/Detroit"

    def start_requests(self):
        """
        We use a headless browser (scrapy-playwright) to handle our request
        because the agency's website uses JavaScript to render the events page.
        """
        yield scrapy.Request(
            url="https://www.riderta.com/events",
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div.fc-scroller")
                ],
            },
            callback=self.parse,
        )

    def parse(self, response):
        """
        Parse the JavaScript-rendered calendar and loop over each <a> tag
        to follow the link to the event page.
        """
        # Navigate through the containers and select each <a> tag
        events = response.css("div.fc-day-grid a.fc-day-grid-event")
        for event in events:
            title = event.css("span.fc-title::text").extract_first()
            href = event.css("::attr(href)").extract_first()
            # this agency includes many events that aren't meetings
            # (eg. career days) so we are explicit in the pages we follow
            if re.search(r"meeting", title, re.IGNORECASE):
                yield response.follow(href, self.parse_event, meta={"title": title})

    def parse_event(self, response):
        """
        Parse the event page for the meeting details.
        """
        title = response.meta["title"]
        start, end = self._parse_date(response)
        meeting = Meeting(
            title=title,
            description="",
            classification=self._parse_classification(title),
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        return meeting

    def _parse_date(self, response):
        """
        Targets a node with a date string in format
        "Wed, May 29 2024, 9 - 10am"
        and extracts the start datetime and end datetime of the
        meeting in timezone naive format. Note that times
        can be in several forms. eg. "9am - 10am" or "9 - 10am" or
        "9am - 1pm" or "9 - 10pm"
        """
        target_str = response.css(
            "div.views-field-field-event-date h2::text"
        ).extract_first()
        try:
            date_parts = target_str.split(",")
            date_str = date_parts[1].strip()
            start_str = date_parts[2].split("-")[0].strip()
            end_str = date_parts[2].split("-")[1].strip()
        except IndexError:
            self.logger.error("Failed to parse date string: %s", target_str)
            return None, None
        # start datetime
        # If 'am' or 'pm' is in the start time, parse
        # the datetime string normally. Otherwise, use
        # any 'am' or 'pm' in the end time to determine.
        # Otherwise, default to 'am'
        if re.search(r"am|pm", start_str, re.IGNORECASE):
            start_datetime_str = f"{date_str} {start_str}"
            start_datetime = parse(start_datetime_str)
        elif re.search(r"am|pm", end_str, re.IGNORECASE):
            regex_am_or_pm = re.compile(r"[a-zA-Z]+")
            am_or_pm = regex_am_or_pm.search(end_str).group()
            start_datetime = parse(f"{date_str} {start_str} {am_or_pm}")
        else:
            start_datetime = parse(f"{date_str} {start_str} am")

        # end datetime
        # If 'am' or 'pm' is in the end time, parse
        # the datetime string normally. Otherwise,
        # default to 'am'
        if re.search(r"am|pm", end_str, re.IGNORECASE):
            end_datetime = parse(f"{date_str} {end_str}")
        else:
            end_datetime = parse(f"{date_str} {end_str} am")
        return start_datetime, end_datetime

    def _parse_classification(self, title):
        """
        Classify the event based on the title.
        """
        if re.search(r"board", title, re.IGNORECASE):
            return BOARD
        elif re.search(r"committee", title, re.IGNORECASE):
            return COMMITTEE
        elif re.search(r"advisory", title, re.IGNORECASE):
            return ADVISORY_COMMITTEE
        return NOT_CLASSIFIED

    def _parse_location(self, response):
        """
        Parse the location of the event.
        """
        # Create a selector for the paragraph containing the address
        address_parts = response.css("p.address span")
        if not address_parts:
            self.logger.info("No address found - default to an undefined location")
            return {
                "name": "TBD",
                "address": "",
            }

        # Combine the address parts
        address = ", ".join(
            [
                part.css("::text").extract_first(default="").strip()
                for part in address_parts
            ]
        ).strip()

        # Format state and zip code from "OH, 44115" to "OH 44115"
        pattern = r"([A-Z]{2}), (\d{5})"
        address = re.sub(pattern, r"\1 \2", address)

        # Extract the first part as the name
        name = address_parts[0].css("::text").extract_first(default="TBD").strip()

        return {
            "name": name,
            "address": address,
        }

    def _parse_links(self, response):
        # Select the container that holds the documents
        container_selector = response.css("div.views-element-container")

        # If the container does not exist, return an empty list
        if not container_selector:
            return []

        # Find all list items within the container that contain links
        list_items = container_selector.css("ul li")

        documents = []
        for item in list_items:
            # Extract the title and href attributes from each link
            title = item.css("a::text").get()
            href = item.css("a::attr(href)").get()

            # If either title or href is None (i.e., element not found),
            # continue to the next item
            if title is None or href is None:
                continue

            # Clean up and append to the list
            documents.append({"title": title.strip(), "href": href.strip()})

        return documents
