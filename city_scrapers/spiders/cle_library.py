import re
from collections import defaultdict
from datetime import datetime

import scrapy
from city_scrapers_core.constants import BOARD, COMMISSION, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleLibrarySpider(CityScrapersSpider):
    name = "cle_library"
    agency = "Cleveland Public Library"
    timezone = "America/Detroit"
    start_urls = [
        "https://cpl.org/aboutthelibrary/board-of-trustees/monthly-board-meeting-minutes/"
    ]
    location = {
        "name": "Louis Stokes Wing",
        "address": "525 Superior Ave Cleveland, OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self.minutes_map = self._parse_minutes(response)
        yield scrapy.Request(
            "https://cpl.org/category/meeting/",
            callback=self._parse_meetings_page,
            dont_filter=True
        )

    def _parse_meetings_page(self, response):
        """Parse meetings from results pages"""
        yield from self._parse_meetings(response)

        page_num = response.url.split("/")[-2]
        if page_num.isdigit():
            page_num = int(page_num) + 1
        else:
            page_num = 2
        if page_num <= 3:
            yield scrapy.Request(
                "https://cpl.org/category/meeting/page/{}/".format(page_num),
                callback=self._parse_meetings_page,
                dont_filter=True
            )

    def _parse_meetings(self, response):
        for item in response.css("article"):
            title = self._parse_title(item)
            summary = item.css(".entry-summary p:first-child::text").extract_first()
            if not summary:
                continue
            detail_link = item.css("a")[0].attrib["href"]
            times = self._parse_times(summary)
            if len(times) == 0:
                continue
            end = None
            start = times[0]
            if len(times) > 1:
                end = times[1]
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(summary),
                links=[{
                    "title": "Agenda",
                    "href": detail_link
                }] + self.minutes_map[start.date()],
                source=detail_link,
            )

            meeting["status"] = self._get_status(meeting, text=summary)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_minutes(self, response):
        minutes_map = defaultdict(list)
        for link in response.css(".entry-content a"):
            link_str = " ".join(link.css("*::text").extract())
            link_date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2}, \d{4}", link_str)
            if not link_date_match:
                continue
            link_date = datetime.strptime(link_date_match.group(), "%B %d, %Y").date()
            minutes_map[link_date].append({
                "title": "Minutes",
                "href": response.urljoin(link.attrib["href"]),
            })
        return minutes_map

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css(".entry-title a::text").extract_first().title()
        if "Special" not in title_str:
            return title_str.replace(" Meeting", "")
        return title_str

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        if "Commission" in title:
            return COMMISSION
        return BOARD

    def _parse_times(self, summary):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2},? \d{4}", summary)
        if not date_match:
            return []
        date_str = date_match.group().replace(",", "")
        time_strs = re.findall(r"(\d{1,2}:\d{2} ([apmAPM\.]{2,4}|Noon))", summary)
        time_objs = []
        for time_str, _ in time_strs:
            time_str = time_str.replace(".", "").replace("Noon", "pm").lower()
            time_objs.append(datetime.strptime(" ".join([date_str, time_str]), "%B %d %Y %I:%M %p"))
        return time_objs

    def _parse_location(self, summary):
        """Parse or generate location."""
        if "Lake Shore" in summary:
            return {
                "name": "",
                "address": "17109 Lake Shore Blvd Cleveland, OH 44110",
            }
        return self.location
