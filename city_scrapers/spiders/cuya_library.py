import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CuyaLibrarySpider(CityScrapersSpider):
    name = "cuya_library"
    agency = "Cuyahoga County Public Library"
    timezone = "America/Detroit"
    start_urls = ["https://cuyahogalibrary.org/About-Us/Our-Organization.aspx"]
    location = {
        "name": "Administration Building Auditorium",
        "address": "2111 Snow Rd Parma, OH 44134",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Create even section groupings for each meeting, even though committees are in same el
        sections = []
        for idx, section_group in enumerate(response.css(".list-items")[1:3]):
            if idx == 0:
                sections.append(section_group)
            else:
                section_split = section_group.extract().split("<hr>")
                for split in section_split:
                    sections.append(Selector(text=split))

        for section in sections:
            self._validate_location(section)
            title = self._parse_title(section)
            classification = self._parse_classification(title)
            year_match = re.search(r"\d{4}", " ".join(section.css("h2 *::text").extract()))
            if not year_match:
                continue
            year_str = year_match.group()
            for split_text in section.extract().split("<br>"):
                item = Selector(text=split_text)
                item_text = re.sub(r"\s+", " ", " ".join(item.css("*::text").extract())).strip()
                start = self._parse_start(item_text, year_str)
                if not start:
                    continue

                meeting = Meeting(
                    title=title,
                    description="",
                    classification=classification,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="Details may change, confirm with staff before attending",
                    location=self.location,
                    links=self._parse_links(item, response),
                    source=response.url
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = " ".join(item.css("h2 *::text").extract())
        split_title = [w for w in title_str.split(" ") if w.strip()]
        return " ".join(split_title[1:-1])

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start(self, item_str, year_str):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2} / \d{1,2}:\d{2} [APM]{2}", item_str)
        if not date_match:
            return
        return datetime.strptime(date_match.group() + year_str, "%B %d / %I:%M %p%Y")

    def _validate_location(self, item):
        """Confirm that location hasn't changed, otherwise raise an error"""
        if "Building Auditorium" not in item.extract():
            raise ValueError("Meeting location has changed")

    def _parse_links(self, item, response):
        """Parse or generate links."""
        link_str = item.css("a::attr(href)").extract_first()
        if not link_str:
            return []
        link_href = response.urljoin(link_str)
        link_title = "Materials"
        if "agenda" in link_href.lower():
            link_title = "Agenda"
        elif "board-book" in link_href.lower():
            link_title = "Board Book"
        elif "minutes" in link_href.lower():
            link_title = "Minutes"
        return [{"href": link_href, "title": link_title}]
