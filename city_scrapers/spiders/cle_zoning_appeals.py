from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleZoningAppealsSpider(CityScrapersSpider):
    name = "cle_zoning_appeals"
    agency = "Cleveland Board of Zoning Appeals"
    timezone = "America/Detroit"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    location = {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 516, Cleveland OH 44114",
    }

    @property
    def start_urls(self):
        base_url = "http://planning.city.cleveland.oh.us/bza/cpc.html"
        return [base_url, "{}?ID={}&btn=Change+Year".format(base_url, datetime.now().year - 1)]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        materials_map = self._parse_materials(response)
        for item in response.css("#jumpMenu option"):
            start = self._parse_start(item)
            meeting = Meeting(
                title="Board of Zoning Appeals",
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response) + materials_map[start],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = item.css("*::text").extract_first()
        return datetime.strptime("{} 09:30".format(date_str), "%B %d, %Y %H:%M")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        return [{"title": "Agenda", "href": response.urljoin(item.attrib["value"])}]

    def _parse_materials(self, response):
        """Parse or generate links for materials."""
        link_map = defaultdict(list)
        for option in response.css("#jumpMenu2 option"):
            dt = self._parse_start(option)
            link_map[dt].append({
                "href": response.urljoin(option.attrib["value"]),
                "title": "Materials",
            })
        return link_map
