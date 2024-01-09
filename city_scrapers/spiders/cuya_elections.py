from datetime import datetime
from typing import Tuple

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaElectionsSpider(CityScrapersSpider):
    name = "cuya_elections"
    agency = "Cuyahoga County Board of Elections"
    timezone = "America/Detroit"
    start_urls = [
        "https://boe.cuyahogacounty.gov/calendar?it=Current%20Events&categories=1%7CBoard%20Meeting"  # noqa
    ]
    _month_dict = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    attachments_page = {
        "title": "Board meeting documents",
        "href": "https://boe.cuyahogacounty.gov/about-us/board-meeting-documents",
    }

    def parse(self, response):
        for link in response.css("a.item-link::attr(href)"):
            # The link path is incorrect, so we need to update it
            correct_link = link.get().replace("boe-events/", "calendar/event-details/")
            yield response.follow(correct_link, callback=self._parse_detail)

    def _parse_detail(self, item):
        meeting = Meeting(
            title=self._parse_title(item),
            description=self._parse_description(item),
            classification=self._parse_classification(item),
            start=self._parse_start(item),
            end=self._parse_end(item),
            all_day=self._parse_all_day(item),
            time_notes=self._parse_time_notes(item),
            location=self._parse_location(item),
            links=[self.attachments_page],
            source=self._parse_source(item),
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, item) -> str:
        """Parse or generate meeting title."""
        title = item.css("h1.sf-event-title span::text").get()
        if title is None:
            return ""
        return title.strip()

    def _parse_description(self, item) -> str:
        """Parse or generate meeting description."""
        description = item.css(".sf_colsIn.col-lg-12 p::text").get()
        if description is None:
            return ""
        return description

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return BOARD

    def _to_24h_time(self, time_s: str) -> Tuple[int, int]:
        """Convert 12-hour time to 24-hour time"""
        time_s = time_s.strip()
        time_tokens = time_s.split(":")
        hour = int(time_tokens[0])
        minute = int(time_tokens[1].split(" ")[0])
        if time_s[-2] == "P" and hour != 12:
            hour += 12
        return (hour, minute)

    def _parse_start(self, item) -> datetime:
        """Parse start datetime as a naive datetime object."""
        _parsed_datetime = item.css(".sf_colsIn.col-lg-12 .meta em").get()
        _parsed_datetime = _parsed_datetime.split("<span>")
        _parsed_date = _parsed_datetime[0][4:-8].strip().split(" ")
        _parsed_start = _parsed_datetime[0][-8:].strip()
        _year = int(_parsed_date[2])
        _month = int(self._month_dict.get(_parsed_date[0]))
        _date = int(_parsed_date[1][:-1])
        _start_time: Tuple[int, int] = self._to_24h_time(_parsed_start)
        return datetime(_year, _month, _date, _start_time[0], _start_time[1])

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        _parsed_datetime = item.css(".sf_colsIn.col-lg-12 .meta em").get()
        _parsed_datetime = _parsed_datetime.split("<span>")
        _parsed_date = _parsed_datetime[0][4:-8].strip().split(" ")
        _parsed_end = _parsed_datetime[1][-13:-5].strip()
        _year = int(_parsed_date[2])
        _month = int(self._month_dict.get(_parsed_date[0]))
        _date = int(_parsed_date[1][:-1])
        _end_time: Tuple[int, int] = self._to_24h_time(_parsed_end)
        return datetime(_year, _month, _date, _end_time[0], _end_time[1])

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):
        """Parse or generate location."""
        _parsed_address = item.css("address::text").get()
        if _parsed_address is None:
            _parsed_address = ""
        else:
            _parsed_address = _parsed_address.strip()
        location: dict = {"name": "", "address": _parsed_address}
        if location.get("address") == "":
            location["address"] = "see links and/or source"

        return location

    def _parse_source(self, item):
        """Parse or generate source."""
        return item.url
