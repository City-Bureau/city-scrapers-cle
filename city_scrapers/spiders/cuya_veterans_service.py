import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaVeteransServiceSpider(CityScrapersSpider):
    name = "cuya_veterans_service"
    agency = "Cuyahoga County Veterans Service Commission"
    timezone = "America/Detroit"
    start_urls = ["http://cuyahogavets.org/board-minutes/"]
    location = {
        "name": "Veterans Service Commission, Boardroom",
        "address": "1849 Prospect Ave, Suite 150, Cleveland, OH 44115",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # TODO: Find if upcoming meetings are ever added
        self._validate_location(response)
        self._validate_start_time(response)

        # Pulls minutes from last two most recent years
        for item in response.css(".board-minutes")[:2].css("td"):
            start = self._parse_start(item)
            if not start:
                continue

            meeting = Meeting(
                title="Veterans Service Commission",
                description="",
                classification=COMMISSION,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("*::text").extract())
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        item_text = re.sub(r"\s+", " ", " ".join(item.css("*::text").extract()))
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_text)
        if not date_match:
            return
        return datetime.strptime(
            " ".join([date_match.group().replace(",", ""), "9:30"]), "%B %d %Y %H:%M"
        )

    def _validate_location(self, response):
        description = re.sub(
            r"\s+",
            " ",
            " ".join(response.css(".su-tabs-pane")[:1].css("p::text").extract()),
        )
        if "VSC Boardroom" not in description:
            raise ValueError("Meeting location has changed")

    def _validate_start_time(self, response):
        if "9:30" not in " ".join(
            response.css(".su-tabs-pane")[:1].css("p::text").extract()
        ):
            raise ValueError("Meeting time has changed")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append(
                {
                    # Including just in case agendas are added
                    "title": "Agenda"
                    if "agenda" in link.attrib["href"].lower()
                    else "Minutes",
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
