import re
from datetime import datetime
from math import ceil

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CuyaPortAuthoritySpider(CityScrapersSpider):
    name = "cuya_port_authority"
    agency = "Cleveland-Cuyahoga County Port Authority"
    timezone = "America/Detroit"
    start_urls = [
        "http://www.portofcleveland.com/about-the-port/board-meeting-information/"
    ]
    location = {
        "name": "Port of Cleveland Offices",
        "address": "1100 W 9th St, Suite 100, Cleveland, OH 44113",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self._validate_location(response)
        self._validate_start_time(response)

        # Go through 2 most recent years of meetings
        for row in response.css("article table")[:2].css("tr"):
            items = []
            # If row is split into paragraphs, add as separate items
            if len(row.css("td:first-child p")) > 0:
                cell_list = []
                half_split = ceil(len(row.css("p, td > a")) / 2)
                for idx, el in enumerate(row.css("p, td > a")):
                    if idx < half_split:
                        el_str = el.extract()
                        if isinstance(el_str, list):
                            el_str = " ".join(el.extract())
                        cell_list.append(el_str)
                    else:
                        cell_idx = idx - half_split
                        el_str = el.extract()
                        if isinstance(el_str, list):
                            el_str = " ".join(el.extract())
                        cell_list[cell_idx] += el_str
                for cell in cell_list:
                    items.append(Selector(text=cell))
            else:
                items.append(row)

            for item in items:
                item_str = " ".join(item.css("*::text").extract())
                start = self._parse_start(item_str)
                if not start:
                    continue

                meeting = Meeting(
                    title=self._parse_title(item_str),
                    description="",
                    classification=BOARD,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=self._parse_links(item, response),
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting, text=item_str)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        if "Special" in item_str:
            return "Board of Directors Special Meeting"
        return "Board of Directors"

    def _validate_start_time(self, response):
        description = " ".join(response.css("article p *::text").extract())
        if "8:30" not in description:
            raise ValueError("Meeting start time has changed")

    def _parse_start(self, item_str):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(
            r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", re.sub(r"\s+", " ", item_str)
        )
        if not date_match:
            return
        return datetime.strptime(
            date_match.group().replace(",", "") + " 8:30", "%B %d %Y %H:%M"
        )

    def _validate_location(self, response):
        """Check if location has changed"""
        description = " ".join(response.css("article p *::text").extract())
        if "1100" not in description:
            raise ValueError("Meeting location has changed")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()).strip(),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
