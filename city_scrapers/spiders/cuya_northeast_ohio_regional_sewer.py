import re
from collections import defaultdict
from datetime import datetime, time

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaNortheastOhioRegionalSewerSpider(CityScrapersSpider):
    name = "cuya_northeast_ohio_regional_sewer"
    agency = "Northeast Ohio Regional Sewer District"
    timezone = "America/Detroit"
    allowed_domains = ["www.neorsd.org"]
    start_urls = [
        "https://www.neorsd.org/document-library/?PAGE=2&BUDGETCENTER_ID=NULL&CONTENT_TYPE_ID=NULL&LibraryItem=agenda&Active=1&Archive=1&Search=Submit"  # noqa
    ]
    location = {
        "name": "George J. McMonagle Building, Public Meeting Room",
        "address": "3900 Euclid Ave Cleveland, OH 44115"
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        link_map = self._parse_link_map(response)
        for meeting_date, links in link_map.items():
            meeting = Meeting(
                title="Board of Trustees",
                description="",
                classification=BOARD,
                start=datetime.combine(meeting_date, time(12, 30)),
                end=None,
                all_day=False,
                time_notes="See documents to confirm details",
                location=self.location,
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start_date(self, link_str):
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2},? \d{4}", link_str)
        if not date_match:
            return
        date_str = date_match.group().replace(",", "")
        return datetime.strptime(date_str, "%B %d %Y").date()

    def _parse_link_map(self, response):
        link_map = defaultdict(list)
        for link in response.css("#fileList > tr > td > a"):
            link_str = " ".join(link.css("*::text").extract())
            link_date = self._parse_start_date(link_str)
            if not link_date:
                continue
            if "agenda" in link_str.lower():
                link_title = "Agenda"
            elif "minutes" in link_str.lower():
                link_title = "Minutes"
            else:
                link_title = link_str
            link_map[link_date].append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return link_map
