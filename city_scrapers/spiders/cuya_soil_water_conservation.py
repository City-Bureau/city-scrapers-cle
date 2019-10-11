import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta


class CuyaSoilWaterConservation(CityScrapersSpider):
    name = "cuya_soil_water_conservation"
    agency = "Cuyahoga Soil and Water Conservation District"
    timezone = "America/Detroit"

    @property
    def start_urls(self):
        """Start at calendar pages 2 months back and 2 months into the future"""
        this_month = datetime.now().replace(day=1)
        months = [this_month + relativedelta(months=i) for i in range(-2, 3)]
        return ["https://www.cuyahogaswcd.org/events/" + m.strftime("%Y/%m") for m in months]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".events-calendar td.filled a"):
            item_text = item.css("*::text").extract_first()
            if "SWCD" in item_text:
                yield response.follow(
                    item.attrib["href"], dont_filter=True, callback=self._parse_meeting
                )

    def _parse_meeting(self, response):
        meeting = Meeting(
            title=self._parse_title(response),
            description=self._parse_description(response),
            classification=BOARD,
            start=self._parse_start(response),
            end=self._parse_end(response),
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css(".lucy-page h2::text").extract_first()
        if "SWCD Board" in title_str:
            return "Board of Supervisors"
        return re.sub(r" Meeting$", "", title_str).strip()

    def _parse_description(self, response):
        """Parse or generate meeting description."""
        return "\n".join(
            line.strip()
            for line in response.css("article p:not(.when-where) *::text").extract()
            if "to calendar" not in line
        )

    def _parse_start(self, response):
        """Parse start datetime as a naive datetime object."""
        date_str = "".join(response.url.split("/")[-4:-1])
        when_str = " ".join(response.css(".when-where *::text").extract())
        time_str = "12:00am"
        time_match = re.search(r"\d{1,2}:\d{2}[apm]{2}", when_str)
        if time_match:
            time_str = time_match.group()
        return datetime.strptime(date_str + time_str, "%Y%m%d%I:%M%p")

    def _parse_end(self, response):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        date_str = "".join(response.url.split("/")[-4:-1])
        when_str = " ".join(response.css(".when-where *::text").extract())
        time_matches = re.findall(r"\d{1,2}:\d{2}[apm]{2}", when_str)
        if len(time_matches) < 2:
            return
        return datetime.strptime(date_str + time_matches[1], "%Y%m%d%I:%M%p")

    def _parse_location(self, response):
        """Parse or generate location."""
        when_where = response.css(".when-where::text").extract()
        addr_str = [line.strip() for line in when_where if re.search(r"\d{3}", line)][0]
        addr_parts = addr_str.split(", ")
        loc_name = ""
        if len(addr_parts) > 2:
            loc_name = addr_parts[0]
            loc_addr = ", ".join(addr_parts[1:])
        else:
            loc_addr = addr_str
        return {
            "name": loc_name,
            "address": re.sub(r"ohio(?= \d)", "OH", loc_addr, flags=re.I),  # Fix Ohio typos
        }

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css(".related-resources a"):
            link_href = link.attrib["href"]
            link_title = link_href.split("/")[-1]
            if "agenda" in link_title:
                link_title = "Agenda"
            elif "minutes" in link_title:
                link_title = "Minutes"
            links.append({
                "title": link_title,
                "href": response.urljoin(link_href),
            })
        return links
