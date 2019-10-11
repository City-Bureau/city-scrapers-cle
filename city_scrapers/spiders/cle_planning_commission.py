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
    start_urls = ["http://planning.city.cleveland.oh.us/designreview/schedule.php"]
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
        agenda_dates = []
        for option in response.css("#jumpMenu option"):
            if not option.attrib["value"].strip():
                continue
            agenda_dates.append(self._parse_agenda_url_start(option.attrib["value"]).date())
            yield scrapy.Request(
                response.urljoin(option.attrib["value"]),
                callback=self._parse_agenda,
            )
        yield from self._parse_table_rows(response, agenda_dates)

    def _parse_table_rows(self, response, agenda_dates):
        for row in response.css(".agendaTable")[0].css("tr"):
            for row_start in self._parse_table_starts(row, str(agenda_dates[0].year)):
                if row_start.date() in agenda_dates:
                    continue
                meeting = Meeting(
                    title="City Planning Commission",
                    description="",
                    classification=COMMISSION,
                    start=row_start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=[],
                    source=response.url,
                )
                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_agenda(self, response):
        meeting = Meeting(
            title="City Planning Commission",
            description="",
            classification=COMMISSION,
            start=self._parse_agenda_url_start(response.url),
            end=None,
            all_day=False,
            time_notes="",
            location=self.location,
            links=self._parse_links(response),
            source=response.url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_agenda_url_start(self, url):
        """Parse agenda start datetime from select option value"""
        date_str = url.split("/")[-2]
        return datetime.strptime(date_str + "9", "%m%d%Y%H")

    def _parse_table_starts(self, row, year):
        """Get start dates from table rows"""
        month = row.css("strong::text").extract_first().replace(".", "")
        starts = []
        for date_cell in row.css("td:not(:first-child)::text").extract():
            date_str = re.sub(r"[^\d]", "", date_cell)
            if not date_str:
                continue
            starts.append(datetime.strptime(" ".join([year, month, date_str, "9"]), "%Y %b %d %H"))
        return starts

    def _parse_links(self, response):
        """Parse or generate links."""
        pdf_link = response.css(".container .d-inline:nth-child(2) a")
        if len(pdf_link):
            return [{"href": response.urljoin(pdf_link[0].attrib["href"]), "title": "Agenda"}]
        return []
