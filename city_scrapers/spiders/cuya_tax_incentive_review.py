import re
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaTaxIncentiveReviewSpider(CityScrapersSpider):
    name = "cuya_tax_incentive_review"
    agency = "Cuyahoga County Tax Incentive Review Council"
    timezone = "America/Detroit"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Tax-Incentive-Review-Council.aspx"]
    location = {
        "name": "Cuyahoga County Headquarters",
        "address": "2079 East 9th Street, Room 2-114, Cleveland, OH 44115",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css("#contentColumn table")[-1:].css("tr")[1:]:
            start = self._parse_start(item)
            if not start:
                continue
            meeting = Meeting(
                title=self._parse_title(item),
                description="",
                classification=ADVISORY_COMMITTEE,
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

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return (
            "Tax Incentive Review Council - "
            + " ".join(item.css("td:nth-child(3) *::text").extract()).strip()
        )

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join(item.css("td:first-child *::text").extract()).strip()
        if not date_str:
            return
        time_el_str = " ".join(item.css("td:nth-child(2) *::text").extract()).strip()
        time_str = "12:00am"
        if time_el_str:
            time_str = time_el_str
        return datetime.strptime(date_str + time_str, "%m/%d/%y%I:%M%p")

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_str = " ".join(item.css("td:nth-child(4) *::text").extract())
        if "2079" in loc_str:
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
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()).strip(),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
