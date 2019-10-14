import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CuyaSoldiersSailorsMonumentSpider(CityScrapersSpider):
    name = "cuya_soldiers_sailors_monument"
    agency = "Cuyahoga County Soldiers and Sailors Monument Commission"
    timezone = "America/Detroit"
    start_urls = ["http://www.soldiersandsailors.com/meeting.htm"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Split notice section into separate selectors by hr tags
        items = [
            Selector(text=section)
            for section in re.split(r"\<hr\s*/?\>", " ".join(response.css(".box4 > *").extract()))
        ]
        for item in items:
            item_str = re.sub(r"\s+", " ", " ".join(item.css("*::text").extract()))
            title = self._parse_title(item_str)
            if not title:
                continue
            classification = self._parse_classification(title)
            meeting = Meeting(
                title=title,
                description="",
                classification=classification,
                start=self._parse_start(item_str),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item_str),
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting, text=item_str)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        if "Notice" not in item_str:
            return
        title_match = re.search(r"(?<=Notice of ).*?(?= Meeting)", item_str)
        if not title_match:
            return "Commission"
        return title_match.group()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Committee" in title:
            return COMMITTEE
        return COMMISSION

    def _parse_start(self, item_str):
        """Parse start datetime as a naive datetime object."""
        # Replace Noon with PM
        item_str = re.sub(r" [Nn]oon", "pm", item_str)
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_str)
        time_match = re.search(r"\d{1,2}:\d{2} ?[APMapm\.]{2,4}", item_str)
        time_str = "12:00am"
        if not date_match:
            return
        date_str = date_match.group().replace(",", "")
        if time_match:
            time_str = re.sub(r"(\s+|\.)", "", time_match.group()).lower()
        return datetime.strptime(" ".join([date_str, time_str]), "%B %d %Y %I:%M%p")

    def _parse_location(self, item_str):
        """Parse or generate location."""
        loc_match = re.search(r"(?<= )[0-9]{1,6} [a-zA-Z0-9,\s]+ [0-9]{5}", item_str)
        if loc_match:
            return {
                "name": "",
                "address": re.sub(r"Ohio(?= \d)", "OH", loc_match.group()),
            }
        return {"name": "TBD", "address": ""}
