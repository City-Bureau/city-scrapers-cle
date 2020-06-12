import re
from collections import defaultdict
from datetime import datetime, time

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaPlanningSpider(CityScrapersSpider):
    name = "cuya_planning"
    agency = "Cuyahoga County Planning Commission"
    timezone = "America/Detroit"
    start_urls = ["https://www.countyplanning.us/about/meetings/"]
    location = {
        "name": "County Headquarters, Conference Room 4-407",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._validate_location(response)

        item_str_map = {}
        link_date_map = self._parse_links(response)
        date_list = []
        for item in response.css(".entry-content .large-12 li"):
            start = self._parse_start(item)
            if start:
                date_list.append(start)
                item_str_map[start] = " ".join(item.css("*::text").extract())

        date_set = set(date_list + list(link_date_map.keys()))
        for start_date in date_set:
            meeting = Meeting(
                title="Planning Commission",
                description="",
                classification=COMMISSION,
                start=datetime.combine(start_date, time(14)),
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=link_date_map[start_date],
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=item_str_map.get(start_date, "")
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start date."""
        item_str = " ".join(item.css("*::text").extract())
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2}, \d{4}", item_str)
        if date_match:
            return datetime.strptime(date_match.group(), "%B %d, %Y").date()

    def _validate_location(self, response):
        desc_str = " ".join(response.css(".entry-content .large-12 *::text").extract())
        if "4-407" not in desc_str and "virtually" not in desc_str:
            raise ValueError("Meeting location has changed")

    def _parse_links(self, response):
        """Parse or generate links."""
        link_date_map = defaultdict(list)
        for row in response.css("aside .textwidget li"):
            row_str = " ".join(row.css("*::text").extract())
            date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2}, \d{4}", row_str)
            if not date_match:
                continue
            date_obj = datetime.strptime(date_match.group(), "%B %d, %Y").date()
            for link in row.css("a"):
                link_title = " ".join(link.css("*::text").extract()).strip()
                link_date_map[date_obj].append(
                    {
                        "title": link_title,
                        "href": response.urljoin(link.attrib["href"]),
                    }
                )
        return link_date_map
