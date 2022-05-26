from datetime import datetime
from typing import Tuple

from city_scrapers_core.constants import COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaMentalHealthResponseSpider(CityScrapersSpider):
    name = "cuya_mental_health_response"
    agency = "Mental Health Response Advisory Committee"
    timezone = "America/Chicago"
    start_urls = [
        "https://www.adamhscc.org/about-us/current-initiatives/task-forces-and-coalitions/mental-health-response-advisory-committee-mhrac"  # noqa
    ]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for i in range(len(response.css("tr"))):
            if i == 0:
                continue  # Skip the first element (table header)
            item = response.css("tr")[i]
            meeting = Meeting(
                title=self._parse_title(item),
                description=self._parse_description(item),
                classification=self._parse_classification(item),
                start=self._parse_start(item),
                end=self._parse_end(item),
                all_day=self._parse_all_day(item),
                time_notes=self._parse_time_notes(item),
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return item.css("span::text").get()

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return COMMITTEE

    def _to_24h_time(self, time_s: str) -> Tuple[int, int]:
        """Helper functionto convert 12-hour time to 24-hour time"""
        time_s = time_s.strip()
        time_tokens = time_s.split(":")
        hour = int(time_tokens[0])
        minute = int(time_tokens[1].split(" ")[0])
        if time_s[-2] == "P" and hour != 12:
            hour += 12
        return (hour, minute)

    def _parse_start_end(self, item) -> dict:
        """Helper function to generate start and end time."""
        parsed_raw_l = item.css("td.event_datetime::text").get().split(" ")
        start_time_24_t = self._to_24h_time(" ".join(parsed_raw_l[1:3]))
        end_time_24_t = self._to_24h_time(" ".join(parsed_raw_l[4:6]))
        parsed_raw_date_l = parsed_raw_l[0].split("/")
        year_i = int(parsed_raw_date_l[2])
        month_i = int(parsed_raw_date_l[0])
        day_i = int(parsed_raw_date_l[1])
        start_time_dt = datetime(
            year_i, month_i, day_i, start_time_24_t[0], start_time_24_t[1]
        )
        end_time_dt = datetime(
            year_i, month_i, day_i, end_time_24_t[0], end_time_24_t[1]
        )
        return {"start": start_time_dt, "end": end_time_dt}

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        return self._parse_start_end(item)["start"]

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return self._parse_start_end(item)["end"]

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):
        """Parse or generate location."""
        return {
            "address": "",
            "name": "Zoom link in meeting links.",
        }

    def _parse_links(self, item):
        """Parse or generate links."""
        href: str = "https://www.adamhscc.org" + item.css("a").attrib["href"]
        return [{"href": href, "title": "Meeting details"}]

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
