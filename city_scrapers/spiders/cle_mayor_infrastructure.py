import re
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CleMayorInfrastructureSpider(CityScrapersSpider):
    name = "cle_mayor_infrastructure"
    agency = "Cleveland Mayor's Infrastructure and Streetscape Advisory Committee"
    timezone = "America/Detroit"
    start_urls = [
        "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules"  # noqa
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
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
        bold_text = " ".join(page_content.css("strong *::text").extract())
        year_match = re.search(r"\d{4}(?= Agenda)", bold_text)
        if year_match:
            year_str = year_match.group()
        else:
            raise ValueError("Year not found")

        content = Selector(text=re.split(r"\<hr.*?\>", page_content.extract())[-2])
        self._validate_start_time(content)
        self._validate_location(content)

        for row in content.css(".report tr"):
            month_str = row.css("td:first-child::text").extract_first().replace(".", "")
            for date_cell in row.css("td:not(:first-child)"):
                start = self._parse_start(date_cell, year_str, month_str)
                if not start:
                    continue
                meeting = Meeting(
                    title="Advisory Committee",
                    description="",
                    classification=ADVISORY_COMMITTEE,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=self._parse_links(date_cell, response),
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _validate_start_time(self, content):
        print(content.extract())
        if "2:00 pm" not in content.extract():
            raise ValueError("Meeting start time has changed")

    def _validate_location(self, content):
        if "City Hall" not in content.extract():
            raise ValueError("Meeting location has changed")

    def _parse_start(self, item, year_str, month_str):
        """Parse start datetime as a naive datetime object."""
        cell_text = " ".join(item.css("* ::text").extract())
        date_text = re.sub(r"\D", "", cell_text)
        if not date_text or "No meeting" in cell_text:
            return
        date_str = " ".join([year_str, month_str, date_text, "2:00pm"])
        return datetime.strptime(date_str, "%Y %b %d %I:%M%p")

    def _parse_links(self, item, response):
        links = []
        for link in item.css("a"):
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()).strip(),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
