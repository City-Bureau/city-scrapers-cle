import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleLandmarksSpider(CityScrapersSpider):
    name = "cle_landmarks"
    agency = "Cleveland Landmarks Commission"
    timezone = "America/Detroit"
    start_urls = [
        "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/LandmarksCommission"  # noqa
    ]
    location = {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        page_content = response.css("#content .field-items .field-item")[0]
        bold_text = " ".join(page_content.css("p strong::text").extract())
        self._validate_location(bold_text)
        self._validate_start_time(bold_text)

        # Should fail if not found
        year_str = re.search(r"\d{4}(?= Agenda)", bold_text).group()

        for item in page_content.css(".report tr"):
            meeting = Meeting(
                title="Landmarks Commission",
                description="",
                classification=COMMISSION,
                start=self._parse_start(item, year_str),
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(
                meeting, text=" ".join(item.css("* ::text").extract())
            )
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _validate_location(self, text):
        """Parse or generate location."""
        if "514" not in text:
            raise ValueError("Meeting location has changed")

    def _validate_start_time(self, text):
        if "9:00 am" not in text:
            raise ValueError("Meeting start time has changed")

    def _parse_start(self, item, year_str):
        cell_str = " ".join(item.css("td:first-child *::text").extract())
        date_str = re.search(r"[A-Z][a-z]{2,9}\s\d{1,2}", cell_str).group()
        return datetime.strptime(" ".join([date_str, "9", year_str]), "%B %d %H %Y")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append({
                "title": " ".join(link.css("*::text").extract()).strip(),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
