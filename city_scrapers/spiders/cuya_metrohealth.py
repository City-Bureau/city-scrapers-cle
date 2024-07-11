import re

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse


class CuyaMetrohealthSpider(CityScrapersSpider):
    name = "cuya_metrohealth"
    agency = "Cuyahoga County MetroHealth System"
    timezone = "America/Detroit"
    start_urls = ["https://www.metrohealth.org/about-us/board-and-governance/meetings"]
    location = {
        "name": "MetroHealth Business Services Building, Board Room K-107",
        "address": "2500 MetroHealth Dr, Cleveland, OH 44109",
    }

    def parse(self, response):
        for detail_link in response.css(".gen-content li a::attr(href)").extract():
            yield response.follow(
                detail_link, callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        # Create meeting items by splitting lines, appending related content
        meeting_items = []
        for el in response.css(".gen-content > *"):
            if el.root.tag == "h3":
                meeting_items.append([el])
            if el.root.tag == "p":
                if meeting_items:
                    meeting_items[-1].append(el)

        # Get meeting items and parse details
        for meeting_item in meeting_items:
            title = meeting_item[0].css("::text").extract_first()
            description = " ".join(
                [el.css("::text").extract_first() for el in meeting_item[1:]]
            )
            # Skip items that don't appear to be meetings
            if not description or "no meeting" in description.lower():
                continue
            clean_description = re.sub(r"\s+", " ", description)
            start = self._parse_start(description)
            if not start:
                continue

            meeting = Meeting(
                title=title,
                description=clean_description,
                classification=self._parse_classification(title),
                start=start,
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

    def _parse_start(self, details):
        date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}(?:,\s\d{4})?\b"  # noqa
        date_match = re.search(date_pattern, details)
        if not date_match:
            return None
        date_str = date_match.group()
        start = parse(date_str)
        return start

    def _parse_classification(self, title):
        if "Board" in title:
            return BOARD
        return COMMITTEE
