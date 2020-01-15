import re
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE, BOARD, COMMITTEE, FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.relativedelta import relativedelta


class CleTransitSpider(CityScrapersSpider):
    name = "cle_transit"
    agency = "Greater Cleveland Regional Transit Authority"
    timezone = "America/Detroit"
    location = {
        "name": "RTA Main Office, Board Room",
        "address": "1240 W 6th St Cleveland, OH 44113",
    }

    @property
    def start_urls(self):
        """Start at calendar pages 2 months back and 2 months into the future"""
        this_month = datetime.now().replace(day=1)
        months = [this_month + relativedelta(months=i) for i in range(-2, 3)]
        return ["http://www.riderta.com/events/" + m.strftime("%Y/%m") for m in months]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for meeting_link in response.css(".field-content a"):
            meeting_title = " ".join(meeting_link.css("*::text").extract())
            if not any(w in meeting_title for w in ["Board", "Committee", "Community", "CAC"]):
                continue
            yield response.follow(
                meeting_link.attrib["href"], callback=self._parse_meeting, dont_filter=True
            )

    def _parse_meeting(self, response):
        """Parse meeting from detail page"""
        title = self._parse_title(response)
        meeting = Meeting(
            title=title,
            description="",
            classification=self._parse_classification(title),
            start=self._parse_start(response),
            end=self._parse_end(response),
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(
            meeting, text=response.css(".panel-flexible-inside")[0].extract()
        )
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = response.css("#page-title::text").extract_first().strip()
        if title_str == "Committee Meetings":
            return "Standing Committees"
        if title_str == "Board and Committee Meetings":
            return "Board of Trustees and Standing Committees"
        if title_str == "Board Meeting":
            return "Board of Trustees"
        if "Community Meeting" in title_str:
            return title_str
        if "CAC" in title_str:
            return "Community Advisory Committee"
        return re.sub(r" Meeting(s)?$", "", title_str)

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Board" in title:
            return BOARD
        elif "Advisory" in title:
            return ADVISORY_COMMITTEE
        elif "Committee" in title:
            return COMMITTEE
        return FORUM

    def _parse_start(self, response):
        """Parse start datetime as a naive datetime object."""
        start_el = response.css(".date-display-start")
        single_el = response.css(".date-display-single")
        if len(start_el) > 0:
            dt_str = start_el[0].attrib["content"][:19]
        elif len(single_el) > 0:
            dt_str = single_el[0].attrib["content"][:19]
        else:
            return
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

    def _parse_end(self, response):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        end_el = response.css(".date-display-end")
        if not len(end_el):
            return
        dt_str = end_el[0].attrib["content"][:19]
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

    def _parse_location(self, response):
        """Parse or generate location."""
        addr_str = " ".join([
            l.strip() for l in response.css(".adr .street-address *::text").extract()
        ]).strip()
        city = response.css(".adr .locality::text").extract_first() or ""
        state = response.css(".adr .region::text").extract_first() or ""
        zip_code = response.css(".adr .postal-code::text").extract_first() or ""
        return {
            "name": (response.css(".adr .fn::text").extract_first() or "").strip(),
            "address":
                "{} {}, {} {}".format(addr_str, city.strip(), state.strip(), zip_code.strip()),
        }

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css(".field-type-file a"):
            links.append({
                "title": " ".join(link.css("*::text").extract()),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
