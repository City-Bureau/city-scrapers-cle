import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaSolidWasteDistrictSpider(CityScrapersSpider):
    name = "cuya_solid_waste_district"
    agency = "Cuyahoga County Solid Waste District"
    timezone = "America/Detroit"
    start_urls = ["https://cuyahogarecycles.org/event_calendar"]
    location = {
        "name": "County Headquarters, Room 5-120",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css(".page-content-row div:nth-child(2)"):
            title = self._parse_title(item)
            start, end = self._parse_start_end(item)
            if not title or not start or ("Board" not in title and "Committee" not in title):
                continue
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self._parse_links(item, response),
                source=self._parse_source(item, response),
            )

            meeting["status"] = self._get_status(meeting, text=" ".join(item.extract()))
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = item.css("div > strong::text").extract_first()
        if not title_str:
            return
        if "board" in title_str.lower():
            return "Board of Directors"
        return title_str.split("]")[-1].strip().replace(" Meeting", "").strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "committee" in title.lower():
            return COMMITTEE
        return BOARD

    def _parse_start_end(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = item.css("h4::text").extract_first()
        if not date_str or not re.search(r"\d{4}", date_str):
            return None, None
        date_str = date_str.strip()
        time_strs = re.findall(r"\d{1,2}:\d{2} [APM]{2}", " ".join(item.css("*::text").extract()))
        start_str = "12:00 AM"
        end = None
        if len(time_strs) > 0:
            start_str = time_strs[0]
        try:
            start = datetime.strptime(date_str + start_str, "%B %d, %Y%I:%M %p")
        except ValueError:
            return None, None
        if len(time_strs) > 1:
            end = datetime.strptime(date_str + time_strs[1], "%B %d, %Y%I:%M %p")
        return start, end

    def _parse_location(self, item):
        """Parse or generate location."""
        loc_strs = [l for l in item.css("div *::text").extract() if re.search(r"\d{3}", l)]
        if len(loc_strs) < 2 or "5-120" in loc_strs[1]:
            return self.location
        return {**self.location, "address": loc_strs[1].strip()}

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            link_title = " ".join(link.css("*::text").extract()).strip()
            if "Learn more" in link_title:
                continue
            if "agenda" in link_title.lower():
                link_title = "Agenda"
            links.append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return links

    def _parse_source(self, item, response):
        """Parse or generate source."""
        source_url = response.url
        for link in item.css("a"):
            if "Learn more" in " ".join(link.css("*::text").extract()):
                source_url = link.attrib["href"]
        return source_url
