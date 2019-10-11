import math
import re
from datetime import datetime, time

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaAdamhsSpider(CityScrapersSpider):
    name = "cuya_adamhs"
    agency = "Cuyahoga County ADAMHS"
    timezone = "America/Detroit"
    start_urls = [
        "http://adamhscc.org/en-US/board-meetings.aspx",
        "http://adamhscc.org/en-US/board-minutes.aspx",
    ]
    location = {"name": "", "address": "2012 W 25th St, 6th Floor Cleveland, OH 44113"}

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        if response.url == self.start_urls[0]:
            yield from self._parse_upcoming(response)
        else:
            yield from self._parse_minutes(response)

    def _parse_minutes(self, response):
        meeting_titles = []
        meeting_selects = []
        for idx, row in enumerate(response.css(".padding table tr")):
            check_idx = idx + 1
            # Ignore every third row
            if check_idx % 3 == 0:
                continue
            if check_idx > 3:
                check_idx = check_idx - math.floor(check_idx / 3)
            if check_idx % 2 == 1:
                meeting_titles.extend([
                    t.strip() for t in row.css("td *::text").extract() if t.strip()
                ])
            elif check_idx % 2 == 0:
                meeting_selects.extend(row.css("select"))
        for title, select in zip(meeting_titles, meeting_selects):
            # Use most recent 3 meetings per category
            for option in select.css("option:not([selected])")[:3]:
                minutes_link = option.attrib["value"]
                if minutes_link == "#":
                    continue
                date_str = option.css("*::text").extract_first().strip()
                start_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                meeting = Meeting(
                    title=title.replace("Faith Based", "Faith-based"),
                    description="",
                    classification=self._parse_classification(title),
                    start=datetime.combine(start_date, time(16)),
                    end=None,
                    all_day=False,
                    time_notes="See meeting source to confirm",
                    location=self.location,
                    links=[{
                        "title": "Minutes",
                        "href": response.urljoin(minutes_link)
                    }],
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_upcoming(self, response):
        for item in response.css(".padding td[style*='background-color']"):
            title = self._parse_title(item)
            start = self._parse_start(item)
            if not title or not start:
                continue
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=None,
                all_day=False,
                time_notes="See meeting source to confirm",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css("strong::text").extract_first().strip()
        if title_str.startswith("NO"):
            return
        if "General" in title_str:
            return title_str
        return title_str + " Committee"

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "General" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        text_items = item.css("*::text").extract()
        date_str = None
        time_str = "12:00 am"
        for text in text_items:
            date_match = re.search(r"\d{1,2}/\d{1,2}/\d{2}", text)
            time_match = re.search(r"\d{1,2}:\d{1,2} [apm]{2}", text)
            if date_match:
                date_str = date_match.group()
            if time_match:
                time_str = time_match.group()
        if not date_str:
            return
        return datetime.strptime(date_str + time_str, "%m/%d/%y%I:%M %p")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append({
                "title": " ".join(link.css("*::text").extract()).strip(),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
