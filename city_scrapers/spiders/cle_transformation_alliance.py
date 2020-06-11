import re
from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import BOARD, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleTransformationAllianceSpider(CityScrapersSpider):
    name = "cle_transformation_alliance"
    agency = "Cleveland Transformation Alliance"
    timezone = "America/Detroit"
    start_urls = ["https://mycleschool.org/category/events/board-of-directors-events/"]
    location = {
        "name": "Cuyahoga Metropolitan Housing Authority",
        "address": "8120 Kinsman Rd, Cleveland, OH 44104",
    }

    def parse(self, response):
        self.board_link_date_map = self._parse_documents(response)
        yield response.follow(
            "/category/events/board-of-directors-events/",
            callback=self._parse_events,
            dont_filter=True,
        )

    def _parse_documents(self, response):
        board_link_date_map = defaultdict(list)
        for row in response.css(".downloads tr"):
            date_str = row.css("td:first-child::text").extract_first()
            link_href = row.css("a::attr(href)").extract_first()
            if not date_str or not link_href:
                continue
            date_obj = datetime.strptime(date_str.strip(), "%m.%d.%Y").date()
            board_link_date_map[date_obj].append(
                {"title": "Board Packet", "href": response.urljoin(link_href)}
            )
        return board_link_date_map

    def _parse_events(self, response):
        for event_link in response.css("article h2 a::attr(href)").extract():
            yield response.follow(
                event_link, callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        title = self._parse_title(response)
        start, end = self._parse_start_end(response)
        classification = self._parse_classification(title)
        if not start:
            return

        meeting = Meeting(
            title=title,
            description="",
            classification=classification,
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(start, classification),
            source=response.url,
        )

        meeting["status"] = self._get_status(
            meeting, text=" ".join(response.css(".post header h1").extract())
        )
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = " ".join(response.css(".post header h1::text").extract()).strip()
        if "Board" in title_str:
            return "Board of Directors"
        return re.sub(
            r"(Transformation Alliance|Meeting)", "", title_str, flags=re.I
        ).strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start_end(self, response):
        """Parse start, end datetimes as naive datetime objects."""
        time_detail = response.css(
            "header .event-date::text, header .post-date::text"
        ).extract()
        detail_time = [p.strip() for p in time_detail if p.strip()]
        if len(detail_time) == 0:
            return None, None
        date_str = detail_time[0]
        start_str = None
        end_str = None
        if len(detail_time) == 2:
            time_str = detail_time[1]
            if "-" in time_str:
                start_str, end_str = time_str.split(" - ")
            else:
                start_str = time_str
        if not start_str:
            desc_str = " ".join(response.css(".post-content *::text").extract())
            time_strs = [
                t[0] for t in re.findall(r"(\d{1,2}(:\d{2})? [apm\.]{2,4})", desc_str)
            ]
            if len(time_strs) > 0:
                start_str = time_strs[0]
            if len(time_strs) > 1:
                end_str = time_strs[1]
        if not start_str:
            start_str = "12:00am"
        start = self._parse_dt_str(date_str + start_str.replace(" ", ""))
        end = None
        if end_str:
            end = self._parse_dt_str(date_str + end_str.replace(" ", ""))
        return start, end

    def _parse_dt_str(self, dt_str):
        dt_fmt = "%B %d, %Y%I%p"
        if ":" in dt_str:
            dt_fmt = "%B %d, %Y%I:%M%p"
        return datetime.strptime(dt_str, dt_fmt)

    def _parse_location(self, response):
        """Parse or generate location."""
        desc_str = (
            re.sub(
                r"\s+", " ", " ".join(response.css(".post-content *::text").extract())
            )
            .replace(" ,", ",")
            .strip()
        )
        if "8120" in desc_str:
            return self.location
        addr_match = re.search(r"\d{3}[^\.:]+?(?=(\.|$))", desc_str)
        if addr_match:
            return {"name": "", "address": addr_match.group()}
        return {"name": "TBD", "address": ""}

    def _parse_links(self, start, classification):
        """Parse or generate links."""
        if classification == BOARD:
            return self.board_link_date_map[start.date()]
        return []
