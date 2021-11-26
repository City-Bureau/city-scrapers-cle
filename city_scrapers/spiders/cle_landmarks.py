import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleLandmarksSpider(CityScrapersSpider):
    name = "cle_landmarks"
    agency = "Cleveland Landmarks Commission"
    timezone = "America/Detroit"
    start_urls = ["https://planning.clevelandohio.gov/landmark/agenda.php"]  # noqa
    location = {
        "name": "YouTube Live Stream",
        "address": "https://www.youtube.com/channel/UCB8ql0Jrhm_pYIR1OLY68bw",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.
        """
        start_time_text = " ".join(response.css("#agendas em::text").extract())
        location_text = " ".join(response.css(".card-body ::text").extract())
        self._validate_location(location_text)
        self._validate_start_time(start_time_text)

        year_text = response.css(".alert h4::text").extract_first()
        year = re.search(r"\d{4}(?= AGENDAS)", year_text).group()
        link_dropdowns = response.css("div.dropdown")
        agenda_links_dict = self._parse_dropdown_links_to_dict(
            link_dropdowns[0], response
        )
        presentation_links_dict = self._parse_dropdown_links_to_dict(
            link_dropdowns[1], response
        )

        table_rows = response.css("tr")

        for row in table_rows:
            month = row.css("td:first-child strong::text").extract_first()[:3]
            for day in row.css("td:not(:first-child)::text").extract():
                if not self._validate_day(day):
                    continue

                agenda_links = self._parse_links_from_dict(
                    month, day, agenda_links_dict
                )
                presentation_links = self._parse_links_from_dict(
                    month, day, presentation_links_dict
                )

                meeting = Meeting(
                    title="Landmarks Commission",
                    description="",
                    classification=COMMISSION,
                    start=self._parse_start(day, month, year),
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=self._parse_links(agenda_links, presentation_links),
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

    def _validate_day(self, day):
        """Cancelled days dont show up but are represented by **"""
        match = re.match(r"[0-9]{1,2}$", day)
        if match:
            return True
        return False

    def _parse_start(self, day, month, year):
        return datetime.strptime(" ".join(["9", day, month, year]), "%H %d %b %Y")

    def _parse_links(self, agenda_links, presentation_links):
        """Parse or generate links."""
        links = []
        for name in agenda_links:
            links.append(
                {"title": " ".join(["Agenda", name]), "href": agenda_links[name]}
            )
        for name in presentation_links:
            links.append(
                {
                    "title": " ".join(["Presentation", name]),
                    "href": presentation_links[name],
                }
            )
        return links

    def _parse_dropdown_links_to_dict(self, item, response):
        links = {}
        for link in item.css(".dropdown-item"):
            name = link.css("::text").extract_first()
            link = response.urljoin(link.attrib["href"])
            links[name] = link
        return links

    def _parse_links_from_dict(self, month, day, links_dict):
        filtered = {}
        for name in links_dict:
            split_name = name.split(" ")
            name_month = split_name[0]
            name_day = split_name[1]
            if (month.lower()[:3] == name_month.lower()[:3]) and name_day == day:
                filtered[name] = links_dict[name]
        return filtered
