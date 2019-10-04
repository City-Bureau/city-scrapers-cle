import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION, FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaReentryLeadershipSpider(CityScrapersSpider):
    name = "cuya_reentry_leadership"
    agency = "Greater Cleveland Reentry Leadership Coalition"
    timezone = "America/Detroit"
    allowed_domains = ["reentry.cuyahogacounty.us"]
    start_urls = ["http://reentry.cuyahogacounty.us/en-US/Leadership-Coalition.aspx"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        table_el = response.css("table.right")
        start_time, end_time = self._parse_start_end_times(table_el)
        location = self._parse_location(table_el)
        for item in response.css("table.right li"):
            item_str = " ".join(item.css("*::text").extract())
            title = self._parse_title(item_str)
            date_obj = self._parse_date(item_str)
            if "Holiday" in title or not date_obj:
                continue
            end = None
            if end_time:
                end = datetime.combine(date_obj, end_time)
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=datetime.combine(date_obj, start_time),
                end=end,
                all_day=False,
                time_notes="",
                location=location,
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting, text=item_str)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item_str):
        """Parse or generate meeting title."""
        title_match = re.search(r"(?<=\().*?(?=\))", item_str)
        if title_match:
            return title_match.group().strip()
        return "Leadership Coalition"

    def _parse_date(self, item_str):
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", item_str)
        if not date_match:
            return
        return datetime.strptime(date_match.group().replace(",", ""), "%B %d %Y").date()

    def _parse_start_end_times(self, sel):
        """Parse start, end times"""
        detail_list = [d.strip() for d in sel.css("td::text").extract()]
        start = None
        end = None
        for detail in detail_list:
            time_matches = re.findall(r"\d{1,2}:\d{2} [apm\.]{2,4}", detail)
            if len(time_matches) > 0:
                start = datetime.strptime(time_matches[0].replace(".", ""), "%I:%M %p").time()
            if len(time_matches) > 1:
                end = datetime.strptime(time_matches[1].replace(".", ""), "%I:%M %p").time()
            if start:
                return start, end
        return start, end

    def _parse_classification(self, title):
        if "Community" in title:
            return FORUM
        return COMMISSION

    def _parse_location(self, sel):
        """Parse or generate location."""
        detail_list = [d.strip() for d in sel.css("td::text").extract()]
        loc_name = detail_list[0]
        addr_list = []
        for addr in detail_list[1:]:
            # Stop iterating after seeing times
            if re.search(r"\d{1,2}:\d{2}", addr):
                break
            addr_list.append(addr)
        return {
            "name": loc_name,
            "address": " ".join(addr_list).replace("Ohio", "OH"),
        }
