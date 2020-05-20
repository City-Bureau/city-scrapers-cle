import re
from datetime import datetime

import scrapy
from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class ClePlanningCommissionSpider(CityScrapersSpider):
    name = "cle_planning_commission"
    agency = "Cleveland City Planning Commission"
    timezone = "America/Detroit"
    start_urls = [
        "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules"  # noqa
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
        bold_text = " ".join(page_content.css("strong *::text").extract())
        year_match = re.search(r"\d{4}(?= Agenda)", bold_text)
        if year_match:
            year_str = year_match.group()
        else:
            raise ValueError("Year not found")
        # else:
        #     year_str = str(datetime.now().year)

        content = scrapy.Selector(text=" ".join(re.split(r"\<hr.*?\>", page_content.extract())[:2]))
        self._validate_start_time(content)
        self._validate_location(content)

        for row in content.css(".report tr"):
            month_str = row.css("td:first-child::text").extract_first().replace(".", "")
            for date_cell in row.css("td:not(:first-child)"):
                start = self._parse_start(date_cell, year_str, month_str)
                if not start:
                    continue
                meeting = Meeting(
                    title="City Planning Commission",
                    description="",
                    classification=COMMISSION,
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
        if "9am" not in content.extract():
            raise ValueError("Meeting start time has changed")

    def _validate_location(self, content):
        if "Room 514" not in content.extract():
            raise ValueError("Meeting location has changed")

    def _parse_start(self, item, year_str, month_str):
        """Parse start datetime as a naive datetime object."""
        cell_text = " ".join(item.css("* ::text").extract())
        date_text = re.sub(r"\D", "", cell_text)
        if not date_text or "No meeting" in cell_text:
            return
        date_str = " ".join([year_str, month_str, date_text, "9:00am"])
        return datetime.strptime(date_str, "%Y %b %d %I:%M%p")

    def _parse_links(self, item, response):
        links = []
        for link in item.css("a"):
            links.append({
                "title": " ".join(link.css("*::text").extract()).strip(),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
