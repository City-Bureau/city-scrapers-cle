import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleGatewayEconomicDevelopmentSpider(CityScrapersSpider):
    name = "cle_gateway_economic_development"
    agency = "Gateway Economic Development Corporation of Greater Cleveland"
    timezone = "America/Detroit"
    start_urls = ["https://www.gwcomplex.org/boardmeetings.html"]
    location = {
        "name": "Climaco Law Offices",
        "address": "55 Public Square Suite 1950 Cleveland, Ohio 44113",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        yield from self._parse_meetings(response)
        for meetings_link in response.css(".CSSTableGenerator ~ p a"):
            yield response.follow(
                meetings_link.attrib["href"],
                dont_filter=True,
                callback=self._parse_meetings,
            )

    def _parse_meetings(self, response):
        for item in response.css(".CSSTableGenerator tr"):
            start = self._parse_start(item)
            if not start:
                continue

            meeting = Meeting(
                title=self._parse_title(item),
                description="",
                classification=BOARD,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("*::text").extract())
            )
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        item_str = " ".join(item.css("*::text").extract())
        if "special" in item_str.lower():
            return "Board of Trustees Special Meeting"
        return "Board of Trustees"

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        item_str = re.sub(
            r"\s+",
            " ",
            " ".join(item.css("td:first-child *::text").extract()),
        ).strip()
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2},? \d{4}", item_str)
        if not date_match:
            return
        date_str = date_match.group().replace(",", "")
        time_str = "12:00 AM"
        time_match = re.search(r"\d{1,2}:\d{2} [APM\.]{2,4}", item_str)
        if time_match:
            time_str = time_match.group().replace(".", "")
        return datetime.strptime(date_str + time_str, "%B %d %Y%I:%M %p")

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_str_list = [
            re.sub(r"\s+", " ", loc_str).strip()
            for loc_str in item.css("td:nth-child(2) *::text").extract()
            if loc_str.strip()
        ]
        # Return default location if empty
        if not " ".join(loc_str_list).strip():
            return self.location
        if len(loc_str_list) > 2:
            return {
                "name": loc_str_list[0],
                "address": " ".join(loc_str_list[1:]),
            }
        else:
            return {
                "name": "",
                "address": " ".join(loc_str_list),
            }

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append(
                {
                    "title": "Agenda"
                    if "agenda" in link.attrib["href"].lower()
                    else "Minutes",
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
