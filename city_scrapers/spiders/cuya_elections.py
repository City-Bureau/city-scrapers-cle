import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import FormRequest


class CuyaElectionsSpider(CityScrapersSpider):
    name = "cuya_elections"
    agency = "Cuyahoga County Board of Elections"
    timezone = "America/Detroit"
    allowed_domains = ["boe.cuyahogacounty.us"]
    start_urls = ["https://boe.cuyahogacounty.us/en-US/EventsCalendar.aspx"]
    location = {"name": "Board of Elections", "address": "2925 Euclid Ave, Cleveland, OH 44115"}

    def parse(self, response):
        today = datetime.now()
        payload = {
            "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$ctl00":
                "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$EventsCalendar1$updMainPanel|ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$EventsCalendar1$TabContainer1$tbpDateRange$btnShowDateRange",  # noqa
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$EventsCalendar1$TabContainer1",  # noqa
            "__EVENTARGUMENT": "activeTabChanged:3",
            "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").extract_first(),
            "__VIEWSTATEGENERATOR":
                response.css("#__VIEWSTATEGENERATOR::attr(value)").extract_first(),
            "__EVENTVALIDATION": response.css("#__EVENTVALIDATION::attr(value)").extract_first(),
            "__AjaxControlToolkitCalendarCssLoaded": "",
            "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$EventsCalendar1$TabContainer1$tbpDateRange$txtStartDate":  # noqa
                (today - timedelta(days=200)).strftime("%m/%d/%Y"),
            "ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolderMain$EventsCalendar1$TabContainer1$tbpDateRange$txtEndDate":  # noqa
                (today + timedelta(days=10)).strftime("%m/%d/%Y"),
            "ContentPlaceHolder1_ContentPlaceHolderMain_EventsCalendar1_TabContainer1_ClientState":
                '{"ActiveTabIndex":3,"TabState":[true,true,true,true]}',
        }
        yield FormRequest(response.url, formdata=payload, callback=self._parse_form_response)

    def _parse_form_response(self, response):
        for link in response.css(".SearchResults td:nth-child(2) a"):
            link_text = " ".join(link.css("*::text").extract())
            # TODO: Include other notices?
            if "Board" not in link_text:
                continue
            yield response.follow(
                link.attrib["href"], callback=self._parse_detail, dont_filter=True
            )

    def _parse_detail(self, response):
        """
        `_parse_detail` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        start, end = self._parse_start_end(response)
        meeting = Meeting(
            title=self._parse_title(response),
            description="",
            classification=BOARD,
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url
        )

        meeting["status"] = self._get_status(
            meeting, text=" ".join(response.css(".padding *::text").extract())
        )
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title_str = " ".join(response.css(".padding h1 *::text").extract())
        if "Special" in title_str:
            return title_str
        return "Board of Elections"

    def _parse_start_end(self, response):
        """Parse start, end datetimes as naive datetime objects."""
        dt_list = []
        for item_str in response.css(".padding dd::text").extract():
            dt_match = re.search(r"\d{1,2}/\d{1,2}/\d{4}-\d{1,2}:\d{2} [APM]{2}", item_str)
            if dt_match:
                dt_list.append(datetime.strptime(dt_match.group(), "%m/%d/%Y-%I:%M %p"))
        end = None
        if len(dt_list) > 1:
            end = dt_list[1]
        return dt_list[0], end

    def _parse_location(self, response):
        """Parse or generate location."""
        detail_strs = response.css(".padding blockquote dd::text").extract()
        loc_str = None
        for detail_str in detail_strs:
            if re.search(r" \d{3}", detail_str):
                loc_str = re.sub(r"\s+", " ", detail_str).strip()
        if loc_str:
            return {"name": "", "address": loc_str}
        return self.location

    def _parse_links(self, response):
        """Parse or generate links."""
        links = []
        for link in response.css(".padding blockquote a"):
            link_title = " ".join(link.css("*::text").extract()).strip()
            links.append({
                "title": link_title,
                "href": response.urljoin(link.attrib["href"]),
            })
        return links
