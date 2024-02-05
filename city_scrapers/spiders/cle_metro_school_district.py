import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleMetroSchoolDistrictSpider(CityScrapersSpider):
    name = "cle_metro_school_district"
    agency = "Cleveland Metropolitan School District"
    timezone = "America/Detroit"
    start_urls = ["https://www.boarddocs.com/oh/cmsd/board.nsf/XML-ActiveMeetings"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.xpath("//meeting"):
            agenda_url = item.xpath("./link/text()").extract_first()
            links = []
            if agenda_url:
                links = [{"title": "Agenda", "href": agenda_url}]
            meeting = Meeting(
                title=self._parse_title(item),
                description="",
                classification=self._parse_classification(item),
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=links,
                source=agenda_url or response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = (
            item.xpath("./name/text()")
            .extract_first()
            .replace("Cleveland Municipal School District ", "")
        )
        return "-".join(title_str.split("-")[:-1]).strip()

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        title_str = item.xpath("./name/text()").extract_first()
        if "Community" in title_str:
            return FORUM
        return BOARD

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        title_str = item.xpath("./name/text()").extract_first()
        time_str = "12:00 AM"
        time_match = re.search(r"\d{1,2}:\d{1,2} *[APM\.]{2,4}", title_str)
        if time_match:
            time_str = time_match.group().replace(".", "")
        date_str = item.xpath("./start/date/text()").extract_first()
        return datetime.strptime(" ".join([date_str, time_str]), "%Y-%m-%d %I:%M %p")

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_item = (
            item.xpath("./category[@order='1']/agendaitems/item/name/text()")
            .extract_first()
            .strip()
        )
        loc_str = re.sub(r"^\d{1,2}\.\d{1,2} ?", "", loc_item)
        loc_parts = re.split(r", ?(?=\d{2})", loc_str, 1)
        if len(loc_parts) == 2:
            return {
                "address": loc_parts[1],
                "name": loc_parts[0],
            }
        if "Board of Education Administration" in loc_parts[0]:
            return {
                "address": "1111 Superior Ave E, Cleveland, OH 44114",
                "name": loc_parts[0],
            }
        if re.search(r"^\d{2,4}", loc_parts[0]):
            return {
                "address": loc_parts[0],
                "name": "",
            }
        else:
            return {
                "address": "",
                "name": loc_parts[0],
            }
