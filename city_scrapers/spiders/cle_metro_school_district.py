import json
from datetime import datetime

from city_scrapers_core.constants import NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from requests import Session


class CleMetroSchoolDistrictSpider(CityScrapersSpider):
    name = "cle_metro_school_district"
    agency = "Cleveland Metropolitan School District"
    timezone = "America/Detroit"
    start_urls = ["https://go.boarddocs.com/oh/cmsd/Board.nsf/Public"]

    def parse(self, response):
        session = Session()
        json_response = session.post(
            url="https://go.boarddocs.com/oh/cmsd/Board.nsf"
            "/BD-GetMeetingsList?open&0.01411260163957615",
            data={"current_committee_id": "A9HCRJ3251CA"},
        )
        meetings = json.loads(json_response.text)

        """
        Sample JSON item

        {'current': '',
        'name': 'Cleveland Municipal School District Work Session Meeting - 6:30 '
                'P.M.',
        'numberdate': '20090210',
        'preliveoak': '1',
        'unid': '49915970A892CAF2852576F5001D114D',
        'unique': '842LYP1D114D'}
        """

        for m in meetings:
            meeting = Meeting(
                title=self._parse_title(m),
                description="",
                classification=self._parse_classification(m),
                start=self._parse_start(m),
                end=None,
                all_day=False,
                time_notes="",
                location="",
                links=self._parse_links(m),
                source=self._parse_source(response),
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, m):
        """Parse or generate meeting title."""
        title = m.get("name")
        if title:
            title = title.rsplit(" -", 1)[0]
            return title
        else:
            return ""

    def _parse_start(self, m):
        """Parse start datetime as a naive datetime object."""
        date_str = m.get("numberdate")
        time_str = m.get("name")
        if time_str:
            time_str = time_str.rsplit("- ", 1)[1]
            time_str = time_str.replace(".", "")

        date_obj = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %I:%M %p")
        return date_obj

    def _parse_classification(self, m):
        """Parse or generate classification from allowed options."""
        return NOT_CLASSIFIED

    def _parse_links(self, m):
        """Parse or generate links."""
        meeting_id = m.get("unique")
        if meeting_id:
            url = "https://go.boarddocs.com/oh/cmsd/Board.nsf/goto?open&id="
            url += meeting_id
            return [{"href": url, "title": f"{self._parse_title(m)}"}]
        else:
            return []

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
