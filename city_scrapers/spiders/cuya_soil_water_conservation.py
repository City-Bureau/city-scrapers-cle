import re

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse as dateparse


class CuyaSoilWaterConservation(CityScrapersSpider):
    name = "cuya_soil_water_conservation"
    agency = "Cuyahoga Soil and Water Conservation District"
    timezone = "America/Detroit"
    start_urls = ["https://cuyahogaswcd.org/events/?category_filter%5B%5D=1"]
    location = {
        "name": "Cuyahoga SWCD office",
        "address": "3311 Perkins Ave, Suite 100, Cleveland, OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".fltrlist--contents a.list--card"):
            meeting_title = item.css("h4::text").extract_first()
            if "SWCD" in meeting_title:
                yield response.follow(item.attrib["href"], callback=self._parse_meeting)

    def _parse_meeting(self, response):
        meeting = Meeting(
            title=self._parse_title(response),
            description=self._parse_description(response),
            classification=BOARD,
            start=self._parse_start(response),
            end=None,
            all_day=False,
            time_notes="",
            location=self.location,
            links=[],
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css(".pgintro--text h1::text").extract_first()
        return title_str.strip()

    def _parse_start(self, response):
        """Parse start datetime as a naive datetime object."""
        start_str = response.css(".pgintro--text > p::text").extract_first()
        clean_start_str = re.sub(r"\s+", " ", start_str).replace("|", ",")
        return dateparse(clean_start_str, fuzzy=True)

    def _parse_description(self, response):
        """Parse or generate meeting description."""
        desc_els = response.css(".pgintro--text div p::text").extract()
        return "\n".join([d.strip() for d in desc_els])
