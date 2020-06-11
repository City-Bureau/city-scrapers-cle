import re
from datetime import datetime

from city_scrapers_core.items import Meeting


class CuyaCountyMixin:
    timezone = "America/Detroit"
    location = {
        "name": "County Headquarters",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def parse(self, response):
        for detail_link in response.css(
            ".gridViewStyle td:nth-child(2) a::attr(href)"
        ).extract():
            yield response.follow(
                detail_link, callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        """Yield a meeting from an individual event page"""
        title = self._parse_title(response)
        start, end = self._parse_start_end(response)
        meeting = Meeting(
            title=title,
            description=self._parse_description(response),
            classification=self._parse_classification(title),
            start=start,
            end=end,
            time_notes="",
            all_day=False,
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=self._parse_source(response),
        )
        meeting["status"] = self._parse_status(response, meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, response):
        title_str = response.css("#contentColumn h1::text").extract_first().strip()
        if "Special" in title_str:
            return title_str
        return title_str.replace(" Meeting", "").strip()

    def _parse_start_end(self, response):
        dt_strs = [d.strip() for d in response.css("blockquote dd::text").extract()]
        end = None
        start = datetime.strptime(dt_strs[0], "%m/%d/%Y-%I:%M %p")
        if len(dt_strs) > 1:
            try:
                end = datetime.strptime(dt_strs[1], "%m/%d/%Y-%I:%M %p")
            except ValueError:
                pass
        return start, end

    def _parse_description(self, response):
        return ""

    def _parse_classification(self, title):
        return self.classification

    def _parse_location(self, response):
        detail_strs = response.css("blockquote dd::text").extract()
        loc_str = None
        for detail_str in detail_strs:
            if re.search(r" \d{3}", detail_str):
                loc_str = re.sub(r"\s+", " ", detail_str).strip()
        return loc_str

    def _parse_links(self, response):
        links = []
        for link in response.css("blockquote a"):
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        for iframe in response.css(".embed-container iframe"):
            links.append({"title": "Video", "href": iframe.attrib["src"]})
        return links

    def _parse_source(self, response):
        return response.url

    def _parse_status(self, response, meeting):
        return self._get_status(meeting)
