import json
from datetime import datetime, timedelta

from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CuyaCountyCouncilSpider(CityScrapersSpider):
    name = "cuya_county_council"
    agency = "Cuyahoga County Council"
    timezone = "America/Detroit"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Content-Type": "application/json"}}
    location = {
        "address": "4th Floor 2079 East 9th Street",
        "name": "C. Ellen Connally Council Chambers"
    }

    @property
    def start_urls(self):
        start_date = datetime.now() + timedelta(days=-90)
        end_date = datetime.now() + timedelta(days=90)
        return [(
            "http://council.cuyahogacounty.us/api/items/GetItemsByType?itemTypeCode="
            "EVENT;NEWS;EVENTREG&languageCd=en-US&siteKey=141&"
            "returnEventsAfterDate={}&returnEventsBeforeDate={}"
        ).format(start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y"))]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        data = json.loads(response.text)
        for item in data:
            start, end = self._parse_start_end(item)
            meeting = Meeting(
                title=self._parse_title(item),
                description="",
                classification=CITY_COUNCIL,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(item),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        header_items = [i for i in item["Characteristics"] if i["TypeCode"] == "HEADER"]
        return header_items[0]["StringValue"].replace("amp;", "")

    def _parse_start_end(self, item):
        start = datetime.strptime(item["StartDate"], "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(item["EndDate"], "%Y-%m-%dT%H:%M:%S")
        if end <= start:
            end = None
        return start, end

    def _parse_location(self, item):
        """Parse or generate location."""
        addr_items = [i for i in item["Characteristics"] if i["TypeCode"] == "ADD"]
        if len(addr_items) == 0:
            return self.location
        addr_str = addr_items[0]["StringValue"]
        addr_split = addr_str.split("-")
        loc_name = ""
        if len(addr_split) > 1:
            loc_name = addr_split[0].strip()
            loc_addr = "-".join(addr_split[1:]).strip()
        else:
            loc_addr = addr_split[0].strip()
        if "Cleveland" not in loc_addr:
            loc_addr += " Cleveland, OH 44115"
        return {
            "name": loc_name,
            "address": loc_addr,
        }

    def _parse_links(self, item):
        """Parse or generate links."""
        links = []
        link_items = [i for i in item["Characteristics"] if i["DataType"] == "F" and i["FileName"]]
        for link_item in link_items:
            if link_item["TypeCode"] == "BAGENDA":
                links.append({
                    "title": "Agenda",
                    "href": (
                        "{}ViewFile.aspx?file={}".format(item["SiteBaseUrl"], link_item["FileKey"])
                    ),
                })
        body_item = [i for i in item["Characteristics"] if i["TypeCode"] == "BODY"][0]
        body = Selector(text=body_item["StringValue"])
        for iframe in body.css("iframe"):
            links.append({
                "title": "Video",
                "href": iframe.attrib["src"],
            })
        return links

    def _parse_source(self, item):
        """Parse or generate source."""
        return item["SiteBaseUrl"][:-1] + item["PageUrl"]
