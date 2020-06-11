import re
from datetime import datetime

from city_scrapers_core.constants import BOARD, CANCELLED, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CuyaMetrohealthSpider(CityScrapersSpider):
    name = "cuya_metrohealth"
    agency = "Cuyahoga County MetroHealth System"
    timezone = "America/Detroit"
    start_urls = ["https://www.metrohealth.org/about-us/board-and-governance/meetings"]
    location = {
        "name": "MetroHealth Business Services Building, Board Room K-107",
        "address": "2500 MetroHealth Dr, Cleveland, OH 44109",
    }

    def parse(self, response):
        for detail_link in response.css(".gen-content li a::attr(href)").extract():
            yield response.follow(
                detail_link, callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        """
        `_parse_detail` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        # Create meeting items by splitting lines, appending related content
        meeting_items = []
        for el in response.css(".gen-content > *"):
            el_text = el.extract()
            if len(meeting_items) == 0 or (
                not isinstance(el.root, str)
                and el.root.tag == "p"
                and not el.attrib.get("style")
            ):
                meeting_items.append(el_text)
            else:
                meeting_items[-1] += el_text

        for item_text in meeting_items:
            item = Selector(text=item_text)
            start, end = self._parse_start_end(item)
            if not start:
                continue
            title = self._parse_title(item)
            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=end,
                all_day=False,
                time_notes="See source to confirm details",
                location=self.location,
                links=self._parse_links(item, response),
                source=response.url,
            )

            if "Cancel" in item_text:
                meeting["status"] = CANCELLED
            else:
                meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title_str = (
            " ".join(
                item.css(
                    "p:not([style]) > strong::text, p strong > strong::text"
                ).extract()
            )
            .replace("Meeting", "")
            .strip()
        )
        if "Board" not in title_str and "Committee" not in title_str:
            title_str += " Committee"
        return re.sub(r"\s+", " ", title_str).strip()

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        return COMMITTEE

    def _parse_start_end(self, item):
        """Parse start, end datetimes as naive datetime objects."""
        dt_str = " ".join(item.css("p[style] *::text").extract())
        date_match = re.search(r"[a-zA-Z]{3,10} \d{1,2},? \d{4}", dt_str)
        time_match = re.search(r"\d{1,2}(:\d{2})? [apm\.]{2,4}", dt_str)
        time_dur_match = re.search(
            r"\d{1,2}(:\d{2})?( [apm\.]{2,4})? - \d{1,2}(:\d{2})? [apm\.]{2,4}", dt_str
        )
        if not date_match or not (time_match or time_dur_match):
            return None, None
        date_str = date_match.group().replace(",", "")
        if time_dur_match:
            time_dur_str = time_dur_match.group()
            start_str, end_str = [s.replace(".", "") for s in time_dur_str.split(" - ")]
            apm_str = end_str.split(" ")[-1]
            if "m" not in start_str:
                start_str += " " + apm_str
            start_fmt = "%I %p"
            end_fmt = "%I %p"
            if ":" in start_str:
                start_fmt = "%I:%M %p"
            if ":" in end_str:
                end_fmt = "%I:%M %p"
            return (
                datetime.strptime(date_str + start_str, "%B %d %Y" + start_fmt),
                datetime.strptime(date_str + end_str, "%B %d %Y" + end_fmt),
            )
        else:
            time_str = time_match.group().replace(".", "")
            time_fmt = "%I %p"
            if ":" in time_str:
                time_fmt = "%I:%M %p"
            return datetime.strptime(date_str + time_str, "%B %d %Y" + time_fmt), None

    def _parse_links(self, item, response):
        """Parse or generate links."""
        links = []
        for link in item.css("a"):
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links
