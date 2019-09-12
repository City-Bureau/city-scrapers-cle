import re
from datetime import datetime, time

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleTransitCommunityAdvisorySpider(CityScrapersSpider):
    name = "cle_transit_community_advisory"
    agency = "Greater Cleveland Regional Transit Authority Community Advisory Committee"
    timezone = "America/Detroit"
    allowed_domains = ["www.riderta.com"]
    start_urls = ["http://www.riderta.com/CAC"]
    location = {
        "name": "RTA Main Office",
        "address": "1240 W 6th St Cleveland, OH 44113",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        year_str = ""
        for item in response.css(".field-item table")[0].css("td"):
            item_str = " ".join(item.css("*::text").extract()).strip()
            year_match = re.search(r"\d{4}", item_str)
            if year_match:
                year_str = year_match.group()
            title = self._parse_title(item_str)
            start, end = self._parse_times(item_str, title, year_str)
            if start is None:
                continue
            meeting = Meeting(
                title=title,
                description="",
                classification=ADVISORY_COMMITTEE,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(title),
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, text):
        """Parse or generate meeting title."""
        abbrev_map = {
            "CAC": "Community Advisory Committee",
            "ADA": "ADA Committee",
            "TIAC": "Transit Improvement Advisory Committee",
        }
        abbrev_match = re.search(r"[A-Z]{3,4}", text)
        if not abbrev_match or abbrev_match.group() not in abbrev_map:
            return
        return abbrev_map[abbrev_match.group()]

    def _validate_start_times(self, response):
        """Validate that start times haven't changed rather than separately parsing them"""
        contact_table = response.css(".field-item table")[1].extract()
        start_times = [
            full for full, part in re.findall(r"(\d{1,2}(:\d{2})? ?[apm\.]{2,4})", contact_table)
        ]
        if start_times != [
            "8:30 a.m.", "10 a.m.", "9:30 a.m.", "11:00 a.m.", "8:30 a.m.", "10:00 a.m."
        ]:
            raise ValueError("Start times have changed")

    def _parse_times(self, text, title, year_str):
        """Parse start, end datetimes as a naive datetime objects."""
        title_map = {
            "Community Advisory Committee": (time(8, 30), time(10)),
            "ADA Committee": (time(9, 30), time(11)),
            "Transit Improvement Advisory Committee": (time(8, 30), time(10)),
        }
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}", text)
        if not date_match:
            return None, None
        # Handle typo
        date_str = date_match.group().replace("Ocotber", "October")
        date_obj = datetime.strptime(" ".join([date_str, year_str]), "%B %d %Y").date()
        start_time, end_time = title_map.get(title, (time(0), time(0)))
        return datetime.combine(date_obj, start_time), datetime.combine(date_obj, end_time)

    def _parse_location(self, title):
        """Parse or generate location."""
        title_map = {
            "Community Advisory Committee": "Board Room",
            "ADA Committee": "Meeting Room 1",
            "Transit Improvement Advisory Committee": "Meeting Room 1",
        }
        return {**self.location, "name": "{}, {}".format(self.location["name"], title_map[title])}
