import re
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE, BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaNortheastOhioCoordinatingSpider(CityScrapersSpider):
    name = "cuya_northeast_ohio_coordinating"
    agency = "Northeast Ohio Areawide Coordinating Agency"
    timezone = "America/Detroit"
    start_urls = [
        "https://www.noaca.org/board-committees/noaca-board-and-committees/agendas-and-presentations/-toggle-all",  # noqa
        "https://www.noaca.org/board-committees/noaca-board-and-committees/agendas-and-presentations/-toggle-all/-npage-2",  # noqa
    ]

    def parse(self, response):
        for link in response.css(".title_column a")[1:]:
            yield response.follow(
                link.attrib["href"], callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        title = self._parse_title(response)
        if not title:
            return

        meeting = Meeting(
            title=title,
            description="",
            classification=self._parse_classification(title),
            start=self._parse_dt(response, "startDate"),
            end=self._parse_dt(response, "endDate"),
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        return (response.css("[itemprop='summary']::text").extract_first() or "").strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Advisory" in title or "Council" in title:
            return ADVISORY_COMMITTEE
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_dt(self, response, prop):
        """Parse datetime as a naive datetime object."""
        dt_str = response.css("[itemprop='{}']::attr(datetime)".format(prop)).extract_first()
        if not dt_str:
            return
        return datetime.strptime(dt_str[:16], "%Y-%m-%dT%H:%M")

    def _parse_location(self, response):
        """Parse or generate location."""
        loc_name = " ".join(
            response.css("[itemprop='location'] [itemprop='name'] *::text").extract()
        ).strip()
        loc_addr = re.sub(
            r"\s+", " ", " ".join(response.css("[itemprop='address'] *::text").extract())
        )
        return {
            "name": loc_name,
            "address": re.sub(r" ,", ",", loc_addr).replace(", Ohio", ", OH"),
        }

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css(".detail-content a, .detail-agenda a, .detail-minutes a"):
            link_title = re.sub(r"\s+", " ", " ".join(link.css("*::text").extract())).strip()
            links.append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
