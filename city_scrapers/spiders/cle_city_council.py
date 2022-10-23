from datetime import datetime

from city_scrapers_core.constants import CITY_COUNCIL, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import LegistarSpider


class CleCityCouncilSpider(LegistarSpider):
    name = "cle_city_council"
    agency = "Cleveland City Council"
    timezone = "America/Detroit"
    start_urls = ["https://cityofcleveland.legistar.com/Calendar.aspx"]
    link_types = []

    def parse_legistar(self, events):
        """
        `parse_legistar` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for event in events:

            if self.legistar_start(event) is None:
                start = datetime.strptime("01-01-01 00:00:00", "%y-%m-%d %H:%M:%S")
            else:
                start = self.legistar_start(event)

            print(self.legistar_start(event))
            meeting = Meeting(
                title=event["Name"]["label"],
                description=self._parse_description(event),
                classification=self._parse_classification(event),
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(event),
                links=self.legistar_links(event),
                source=self.legistar_source(event),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        location = item.get("Meeting Location", "")
        if isinstance(location, dict):
            location = location.get("label", "")
        if "--em--" not in location:
            return ""
        return " ".join(location.split("--em--")[1:]).strip()

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        if "committee" in item["Name"]["label"].lower():
            return COMMITTEE
        return CITY_COUNCIL

    def _parse_location(self, item):
        """Parse or generate location."""
        location = item.get("Meeting Location", "")
        if isinstance(location, dict):
            location = location.get("label", "")
        return {
            "address": "601 Lakeside Ave Cleveland OH 44114",
            # Might miss rare edge cases, but will be captured in name
            "name": location.split("--em--")[0],
        }
