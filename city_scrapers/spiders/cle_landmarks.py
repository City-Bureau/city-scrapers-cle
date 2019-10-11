import re
from datetime import datetime, time

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleLandmarksSpider(CityScrapersSpider):
    name = "cle_landmarks"
    agency = "Cleveland Landmarks Commission"
    timezone = "America/Detroit"
    start_urls = ["http://planning.city.cleveland.oh.us/landmark/AGENDALIST.html"]
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
        self._validate_location(response)

        agenda_start_map = self._parse_agenda_starts(response)
        agenda_dates = sorted(list(agenda_start_map.keys()))
        year_str = str(agenda_dates[-1].year)
        start_dates = self._parse_table_starts(response, year_str)
        no_agenda_dates = set(start_dates) - set(agenda_dates)
        agenda_link_dates = set(start_dates + agenda_dates) - no_agenda_dates

        # Yield for start dates without agenda pages
        for start_date in no_agenda_dates:
            yield self._create_meeting(start_date, response)
        for start_date in agenda_link_dates:
            yield response.follow(agenda_start_map[start_date], callback=self._parse_agenda)

    def _parse_agenda(self, response):
        start_date = self._parse_agenda_url_start(response.url)
        yield self._create_meeting(start_date, response, links=self._parse_links(response))

    def _create_meeting(self, start_date, response, links=[]):
        meeting = Meeting(
            title="Landmarks Commission",
            description="",
            classification=COMMISSION,
            start=datetime.combine(start_date, time(9)),
            end=None,
            all_day=False,
            time_notes="",
            location=self.location,
            links=links,
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        return meeting

    def _validate_location(self, response):
        """Parse or generate location."""
        if "514" not in response.text:
            raise ValueError("Meeting location has changed")

    def _parse_table_starts(self, response, year_str):
        """Get start dates from table rows"""
        starts = []
        for row in response.css(".agendaTable tr"):
            month = row.css("strong::text").extract_first().replace(".", "")
            for date_cell in row.css("td:not(:first-child)::text").extract():
                date_match = re.search(r"([a-zA-Z]{3}\s+)?\d{1,2}", date_cell)
                if not date_match:
                    continue
                month_str = month
                date_str = re.sub(r"\s+", " ", date_match.group()).strip()
                if " " in date_str:
                    month_str, date_str = date_str.split(" ")
                starts.append(
                    datetime.strptime(" ".join([year_str, month_str, date_str]), "%Y %b %d").date()
                )
        return starts

    def _parse_agenda_starts(self, response):
        """Parse or generate links."""
        agenda_starts = {}
        # Parse most recent two agenda sections
        for section in response.css(".clcAgenda")[:2]:
            for agenda_link in section.css("a"):
                date_match = re.search(r"\d{8}", agenda_link.attrib["href"])
                if not date_match:
                    continue
                agenda_start = datetime.strptime(date_match.group(), "%m%d%Y").date()
                agenda_starts[agenda_start] = agenda_link.attrib["href"]
        return agenda_starts

    def _parse_agenda_url_start(self, url):
        """Parse agenda start datetime from select option value"""
        date_str = url.split("/")[-2]
        return datetime.strptime(date_str, "%m%d%Y").date()

    def _parse_links(self, response):
        """Parse or generate links."""
        pdf_link = response.css(".container .d-inline:nth-child(2) a")
        if len(pdf_link):
            return [{"href": response.urljoin(pdf_link[0].attrib["href"]), "title": "Agenda"}]
        return []
