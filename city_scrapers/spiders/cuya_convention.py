import re
from collections import defaultdict
from datetime import datetime, time

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaConventionSpider(CityScrapersSpider):
    name = "cuya_convention"
    agency = "Cuyahoga County Convention Facility Development Corporation"
    timezone = "America/Detroit"
    allowed_domains = ["www.cccfdc.org"]
    start_urls = ["http://www.cccfdc.org/"]
    location = {
        "name": "Global Center for Health Innovation, Executive Board Room",
        "location": "1 St. Clair Ave NE Cleveland, OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self.date_links_map = defaultdict(list)
        schedule_text = " ".join(response.css(".downloads-title *::text").extract())
        self._validate_location(schedule_text)
        if "8:00 am" not in schedule_text:
            raise ValueError("Meeting start time has changed")
        year_str = re.search(r"\d{4}", schedule_text).group()
        for date_str in re.findall(r"[A-Z][a-z]{2,9} \d{1,2}(?=[a-z]{2})", schedule_text):
            date_obj = datetime.strptime(date_str + year_str, "%B %d%Y").date()
            # Just setting these dates as keys
            self.date_links_map[date_obj] = []
        self._parse_link_map(response)
        for date_obj, links in self.date_links_map.items():
            meeting = Meeting(
                title="Board of Directors",
                description="",
                classification=BOARD,
                start=datetime.combine(date_obj, time(8)),
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _validate_location(self, schedule_text):
        """Parse or generate location."""
        if "GCHI" not in schedule_text:
            raise ValueError("Meeting location has changed")

    def _parse_link_map(self, response):
        """Parse or generate links."""
        minutes_links = []
        for minutes_link in response.css(".downloads-archived-dropdown option::attr(data-url)"
                                         ).extract():
            minutes_href = response.urljoin(minutes_link)
            if minutes_href in minutes_links:
                continue
            minutes_links.append(minutes_href)
            date_obj = self._parse_link_date(minutes_link)
            if not date_obj:
                continue
            self.date_links_map[date_obj].append({"title": "Minutes", "href": minutes_href})
        for agenda_link in response.css("a.downloads-link-wrap::attr(href)").extract():
            if "agenda" not in agenda_link.lower():
                continue
            date_obj = self._parse_link_date(agenda_link)
            if not date_obj:
                continue
            self.date_links_map[date_obj].append({
                "title": "Agenda",
                "href": response.urljoin(agenda_link)
            })

    def _parse_link_date(self, link):
        """Parse date from multiple formats in links"""
        date_match = re.search(r"\d{1,2}[-_\.]\d{1,2}[-_\.]\d{4}", link)
        if date_match:
            date_str = re.sub(r"[_\.]", "-", date_match.group())
            date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()
        else:
            date_match = re.search(r"[a-zA-Z]{3,9} \d{1,2},? \d{4}", link)
            if not date_match:
                return
            date_str = date_match.group().replace(",", "")
            date_obj = datetime.strptime(date_str, "%B %d %Y").date()
        return date_obj
