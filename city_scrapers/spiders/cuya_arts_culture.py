import re
from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaArtsCultureSpider(CityScrapersSpider):
    name = "cuya_arts_culture"
    agency = "Cuyahoga County Arts & Culture"
    timezone = "America/Detroit"
    start_urls = ["https://www.cacgrants.org/about-us/board/board-materials/"]

    def parse(self, response):
        self._parse_minutes(response)
        yield response.follow(
            "/about-us/board/board-meeting-schedule/",
            callback=self._parse_schedule,
            dont_filter=True,
        )

    def _parse_minutes(self, response):
        """Generate a defaultdict of meeting dates to minutes links (if available)"""
        self.minutes_map = defaultdict(list)
        # Only get the most recent two year groups of minutes
        for item in response.css(".panel")[:2].css("p"):
            meeting_str = " ".join(item.css("strong *::text").extract())
            date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", meeting_str)
            if not date_match:
                return
            date_obj = datetime.strptime(date_match.group(), "%B %d, %Y").date()
            for link in item.css("a"):
                link_title = " ".join(link.css("*::text").extract())
                if "Minutes" in link_title:
                    self.minutes_map[date_obj].append({
                        "title": "Minutes",
                        "href": response.urljoin(link.attrib["href"])
                    })

    def _parse_schedule(self, response):
        """Iterate through all meetings for the current year, yielding request to detail pages"""
        for link in response.css(".panel-body a"):
            if "/maps/" not in link.attrib["href"]:
                yield response.follow(
                    link.attrib["href"], callback=self._parse_detail, dont_filter=True
                )

    def _parse_detail(self, response):
        """
        `_parse_detail` should always `yield` a Meeting item.
        """
        description = self._parse_description(response)
        start = self._parse_start(description)
        if not start:
            return

        meeting = Meeting(
            title=self._parse_title(response),
            description=description,
            classification=BOARD,
            start=start,
            end=None,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response) + self.minutes_map[start.date()],
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css("#headline h1::text").extract_first().strip()
        title_clean = re.sub(r" [a-zA-Z]{3,10} \d{1,2}, \d{4}", "", title_str)
        if title_clean == "Board Meeting":
            return "Board of Trustees"
        return "Board of Trustees " + title_clean

    def _parse_description(self, response):
        """Parse or generate meeting description."""
        desc_list = []
        for desc_item in response.css("#Content_ceContent > p"):
            desc_text = re.sub(r"\s+", " ", " ".join(desc_item.css("*::text").extract())).strip()
            if not desc_text.startswith("View the ") and not desc_text.startswith("Want to "):
                desc_list.append(desc_text)
        return "\n\n".join(desc_list).strip()

    def _parse_start(self, description):
        """Parse start datetime as a naive datetime object."""
        dt_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4} at \d{1,2}:\d{2} [ap]m", description)
        if not dt_match:
            return
        return datetime.strptime(dt_match.group(), "%B %d, %Y at %I:%M %p")

    def _parse_location(self, response):
        """Parse or generate location."""
        name_str = response.css("center h3:last-child::text").extract_first().strip()
        addr_str = ""
        loc_span_str = re.sub(
            r"\s+", " ",
            " ".join(response.css("#Content_ceContent > p > span")[:1].css("*::text").extract())
        ).strip()
        addr_split = re.split(r"(, | at )(?=\d{2}[^:])", loc_span_str)
        if len(addr_split) > 2 and "TBD" not in name_str:
            addr_str = re.sub(r"( at| in|[\.\(\)])", "", addr_split[-1]).strip()
        return {
            "name": name_str,
            "address": addr_str,
        }

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css("#Content_ceContent a"):
            link_title = " ".join(link.css("*::text").extract())
            if ".pdf" in link.attrib["href"].lower():
                if "agenda" in link_title.lower():
                    link_title = "Agenda and Handouts"
                links.append({
                    "title": link_title.strip(),
                    "href": response.urljoin(link.attrib["href"])
                })
        return links
