import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaLandBankSpider(CityScrapersSpider):
    name = "cuya_land_bank"
    agency = "Cuyahoga County Land Bank"
    timezone = "America/Detroit"
    allowed_domains = ["www.cuyahogalandbank.org"]
    start_urls = ["http://www.cuyahogalandbank.org/boardMeetings.php"]
    location = {
        "name": "Caxton Building",
        "address": "812 Huron Road E, Suite 830 Cleveland, OH 44115",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Only pull most recent 10 meetings
        for meeting_link in response.css("#center a")[:5]:
            yield response.follow(
                meeting_link.attrib["href"], dont_filter=True, callback=self._parse_meeting
            )

    def _parse_meeting(self, response):
        start = self._parse_start(response)
        title = self._parse_title(response)
        if not start:
            return

        meeting = Meeting(
            title=title,
            description="",
            classification=self._parse_classification(title),
            start=start,
            end=None,
            all_day=False,
            time_notes="See agenda and notice to confirm details",
            location=self.location,
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(
            meeting, text=" ".join(response.css("#center").extract())
        )
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css("#center h1::text").extract_first().strip()
        title = re.split(r"\d{4} ", title_str)[-1]
        if title == "Board Meeting":
            return "Board of Directors"
        return title

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        return BOARD

    def _parse_start(self, response):
        """Parse start datetime as a naive datetime object."""
        header_str = response.css("#center h1::text").extract_first().strip()
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2},? \d{4}", header_str)
        if not date_match:
            return
        return datetime.strptime(date_match.group().replace(",", "") + "10", "%B %d %Y%H")

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css("#center a"):
            link_text = " ".join(link.css("*::text").extract())
            if "Notice" in link_text:
                link_title = "Notice"
            elif "Agenda" in link_text:
                link_title = "Agenda"
            elif "Minutes" in link_text:
                link_title = "Minutes"
            else:
                resolution_match = re.search(r"(?<=_)\d{1,2}(?=_)", link.attrib["href"])
                if resolution_match:
                    link_title = "Resolution " + resolution_match.group()
                else:
                    link_title = link_text[:50]
            links.append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
