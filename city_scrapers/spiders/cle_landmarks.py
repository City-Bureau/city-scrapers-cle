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
        "https://planning.clevelandohio.gov/landmark/agenda.php"  # noqa
    ]
    location = {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        For this scraper we are looking to extract the following pieces of information:
        location (for validation)
        start_time (for validation)

        and for each meeting:
        year
        start
        links
        """
        page_content = response.css("#cpcwrapper table")[1]
        italics_text = " ".join(page_content.css("p em::text").extract())
        location_text = " ".join(page_content.css("p::text").extract())
        self._validate_location(location_text)
        self._validate_start_time(italics_text)

        year_texts = page_content.css('.divider::text').extract()
        date_tables = page_content.css('.clcAgenda')

        for year_text, date_table in zip(year_texts, date_tables):
            # Should fail if not found
            year_str = re.search(r"\d{4}(?= AGENDAS)", year_text).group()

            for item in date_table.css("tr td"):

                table_text = item.css("::text").extract_first()
                date_match = re.search(r"[A-Z][a-z]{2,9}\s\d{1,2}", table_text)
                if date_match == None:  # some tables have empty rows - we use this check to skip rows without dates
                    continue
                date_str = date_match.group()

                meeting = Meeting(
                    title="Landmarks Commission",
                    description="",
                    classification=COMMISSION,
                    start=self._parse_start(date_str, year_str),
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=self._parse_links(item, response),
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)
                yield meeting

    def _validate_location(self, text):
        """Parse or generate location."""
        if "in a limited capacity using the WebEx Platform" not in text:
            raise ValueError("Meeting location has changed")

    def _validate_start_time(self, text):
        if "9:00 am" not in text:
            raise ValueError("Meeting start time has changed")

    def _parse_start(self, date_str, year_str):
        return datetime.strptime(" ".join([date_str, "9", year_str]), "%B %d %H %Y")

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
