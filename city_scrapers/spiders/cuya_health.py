import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaHealthSpider(CityScrapersSpider):
    name = "cuya_health"
    agency = "Cuyahoga County Board of Health"
    timezone = "America/Detroit"
    start_urls = ["https://www.ccbh.net/board-minutes-agenda/"]
    location = {
        "name": "Cuyahoga County Board of Health",
        "address": "5550 Venture Dr, Parma, OH 44130",
    }

    def parse(self, response):
        """
        Collects a list of meetings from the meetings materials page using
        each agenda link to create a meeting item. Attempts to gorup agenda
        and minute links together based on their link titles.
        """
        meetings_filtered = self._filter_meetings(response)
        for item in meetings_filtered.values():
            meeting = Meeting(
                title=item["title"],
                description="",
                classification=BOARD,
                start=item["start"],
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=item["links"],
                source=response.url,
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _filter_meetings(self, response):
        """
        Filters meetings from the response based on their date and title.

        Skips meetings without a valid href or date and those older than
        6 months. It groups 'agenda' and 'minutes' based on the link title
        and returns a dictionary of meetings with their respective links.
        """
        meetings = {}
        minutes = {}
        for link in response.css(".ea-card .ea-body p a"):
            href = link.attrib["href"]
            link_title = link.css("::text").extract_first()
            start = self.parse_meeting_date(link_title)
            # If the href or date cannot be parsed, skip the link
            if not href or not start:
                continue
            # If the meeting is older than 6 months, skip it
            if self._is_old_meeting(start):
                continue
            meeting_title = self._parse_title(link_title)
            meeting_id_partial = re.sub(r"\s+", "", meeting_title.lower())
            meeting_id = f"{start.date()}_{meeting_id_partial}"
            if "agenda" in link_title.lower():
                date_pretty = start.strftime("%b %d, %Y")
                title = f"{meeting_title} meeting ({date_pretty})"
                meetings[meeting_id] = {
                    "title": title,
                    "href": href,
                    "start": start,
                    "links": [{"href": href, "title": "Agenda"}],
                }
            elif "minutes" in link_title.lower():
                minutes[meeting_id] = {"href": href, "title": "Minutes"}

        # Merge the minutes into the meetings dictionary
        for meeting_id, data in minutes.items():
            if meeting_id in meetings:
                meetings[meeting_id]["links"].append(data)
        return meetings

    def parse_meeting_date(self, meeting_string):
        """
        Parses a meeting date from various string formats and returns a datetime object.
        """
        pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s(\d{1,2}),\s(\d{4})"  # noqa
        match = re.search(pattern, meeting_string)
        if match:
            date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
            meeting_date = datetime.strptime(date_str, "%B %d %Y")
            return meeting_date
        return None

    def _parse_title(self, meeting_string):
        """
        Parses a meeting title from a string, removing the
        date and the words "minutes" or "agenda".
        """
        cleaned_title = re.sub(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}",  # noqa
            "",
            meeting_string,
            flags=re.IGNORECASE,
        )
        cleaned_title = re.sub(
            r"minutes|agenda", "", cleaned_title, flags=re.IGNORECASE
        )
        cleaned_title = cleaned_title.strip()
        return cleaned_title

    def _is_old_meeting(self, provided_date):
        """
        Checks if a provided datetime is older than 6 months from the current date.
        Returns True if the date is older than 6 months, False otherwise.
        """
        six_months_ago = datetime.now() - timedelta(days=30 * 6)
        return provided_date < six_months_ago
