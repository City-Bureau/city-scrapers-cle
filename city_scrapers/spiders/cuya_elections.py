from datetime import datetime
from typing import Tuple

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse


class CuyaElectionsSpider(CityScrapersSpider):
    name = "cuya_elections"
    agency = "Cuyahoga County Board of Elections"
    timezone = "America/Detroit"
    start_urls = [
        "https://boe.cuyahogacounty.gov/calendar?pageSize=96&it=Current+Events"  # noqa
    ]
    attachments_page = {
        "title": "Board meeting documents",
        "href": "https://boe.cuyahogacounty.gov/about-us/board-meeting-documents",
    }

    def parse(self, response):
        for link in response.css(".es-item-list a"):
            # many links on the page are for community events,
            # we only want board meetings
            if "meeting" in link.css("::text").get().lower():
                yield response.follow(link.attrib["href"], callback=self._parse_detail)

    def _parse_detail(self, item) -> Meeting:
        start, end = self._parse_start_end(item)
        meeting = Meeting(
            title=self._parse_title(item),
            description=self._parse_description(item),
            classification=BOARD,
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=self._parse_location(item),
            links=[self.attachments_page],
            source=item.url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, item) -> str:
        """Parse or generate meeting title."""
        title = item.css("h1.sf-event-title span::text").get()
        if title is None:
            return ""
        return title.strip()

    def _parse_start_end(self, item) -> Tuple[datetime, datetime]:
        date_objs = item.xpath("//em/text()").getall()
        start_str = date_objs[0].replace("Date and time: ", "")
        start = parse(start_str)
        if len(date_objs) > 1:
            end_time_str = date_objs[1]
            end_time = parse(end_time_str)
            end = start.replace(hour=end_time.hour, minute=end_time.minute)
            return start, end
        return start, None

    def _parse_description(self, item) -> str:
        """Parse or generate meeting description."""
        description = item.css(".sf_colsIn.col-lg-12 p::text").get().strip()
        if description is None:
            return ""
        return description

    def _parse_location(self, item) -> dict:
        """Parse or generate location."""
        address = item.css("address::text").get()
        if address:
            address = " ".join(address.strip().split())
            return {"name": "", "address": address}
        return {"name": "", "address": ""}
