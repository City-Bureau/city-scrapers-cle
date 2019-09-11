import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleBuildingStandardsSpider(CityScrapersSpider):
    name = "cle_building_standards"
    agency = "Cleveland Board of Building Standards and Building Appeals"
    timezone = "America/Detroit"
    allowed_domains = ["planning.city.cleveland.oh.us"]
    start_urls = ["http://planning.city.cleveland.oh.us/bza/bbs.html"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    location = {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 516, Cleveland OH 44114",
    }

    @property
    def start_urls(self):
        return [
            "http://planning.city.cleveland.oh.us/bza/bbs.html?ID={}".format(diff)
            for diff in range(0, 2)
        ]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._validate_location(response)
        for item in response.css("#jumpMenu option"):
            start = self._parse_start(item)
            if not start:
                continue
            meeting = Meeting(
                title="Board of Building Standards and Building Appeals",
                description="",
                classification=BOARD,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(r"\d{8}", item.attrib["value"])
        if not date_match:
            return
        return datetime.strptime(date_match.group() + "0930", "%m%d%Y%H%M")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        return [{"href": response.urljoin(item.attrib["value"]), "title": "Agenda"}]

    def _validate_location(self, response):
        if "516" not in response.text:
            raise ValueError("Meeting location has changed")
