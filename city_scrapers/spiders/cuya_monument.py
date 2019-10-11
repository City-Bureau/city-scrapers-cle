import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaMonumentSpider(CityScrapersSpider):
    name = "cuya_monument"
    agency = "Cuyahoga County Monument Commission"
    timezone = "America/Detroit"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Monument-Commission.aspx"]
    location = {
        "name": "Cuyahoga County Archives Building, 3rd Floor",
        "address": "3951 Perkins Ave, Cleveland, OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css("#contentColumn table")[-1:].css("tr")[1:]:
            meeting = Meeting(
                title="Monument Commission",
                description="",
                classification=COMMISSION,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        dt_str = re.sub(r"\s+", " ", " ".join(item.css("td:first-child *::text").extract()))
        return datetime.strptime(dt_str, "%m/%d/%Y %I:%M %p")

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_str = " ".join(item.css("td:nth-child(2) *::text").extract())
        if "3951" in loc_str:
            return self.location
        split_loc = re.split(r", (?=\d{2})", loc_str, 1)
        loc_name = ""
        if len(split_loc) > 1:
            loc_name, loc_addr = split_loc[0]
        else:
            loc_addr = split_loc[0]
        if "Cleveland" not in loc_addr:
            loc_addr += " Cleveland, OH"
        return {
            "name": loc_name,
            "address": loc_addr,
        }

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append({
                "title": " ".join(link.css("*::text").extract()).strip(),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
