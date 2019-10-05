import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import FormRequest

from city_scrapers.mixins import CuyaCountyMixin


class CuyaOpiateTaskForceSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_opiate_task_force"
    agency = "Cuyahoga County Opiate Task Force"
    start_urls = ["http://opiatecollaborative.cuyahogacounty.us/en-US/Meeting-Calendar.aspx"]
    classification = COMMISSION
    location = {
        "name": "Cuyahoga County Board of Health",
        "address": "5550 Venture Dr, Parma, OH 44130",
    }

    def parse(self, response):
        today = datetime.now()
        payload = {
            "ctl00$ctl04":
                "ctl00$ContentPlaceHolder1$EventsCalendar1$updMainPanel|ctl00$ContentPlaceHolder1$EventsCalendar1$TabContainer1$tbpDateRange$btnShowDateRange",  # noqa
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$EventsCalendar1$TabContainer1",
            "__EVENTARGUMENT": "activeTabChanged:3",
            "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").extract_first(),
            "__VIEWSTATEGENERATOR":
                response.css("#__VIEWSTATEGENERATOR::attr(value)").extract_first(),
            "__EVENTVALIDATION": response.css("#__EVENTVALIDATION::attr(value)").extract_first(),
            "ctl00$ContentPlaceHolder1$EventsCalendar1$TabContainer1$tbpDateRange$txtStartDate":
                (today - timedelta(days=200)).strftime("%m/%d/%Y"),
            "ctl00$ContentPlaceHolder1$EventsCalendar1$TabContainer1$tbpDateRange$txtEndDate":
                (today + timedelta(days=90)).strftime("%m/%d/%Y"),
            "ctl00_ContentPlaceHolder1_EventsCalendar1_TabContainer1_ClientState":
                '{"ActiveTabIndex":3,"TabState":[true,true,true,true]}',
        }
        yield FormRequest(response.url, formdata=payload, callback=self._parse_form_response)

    def _parse_form_response(self, response):
        for detail_link in response.css(
            ".ajax__tab_panel:last-child .SearchResults td:nth-child(2) a::attr(href)"
        ).extract():
            yield response.follow(detail_link, callback=self._parse_detail, dont_filter=True)

    def _parse_title(self, response):
        title_str = response.css("#rightColumn h1::text").extract_first().strip()
        if "Special" in title_str:
            return title_str
        return title_str.replace(" Meeting", "").strip()

    def _parse_location(self, response):
        detail_strs = response.css("blockquote dd::text").extract()
        loc_str = None
        for detail_str in detail_strs:
            if re.search(r"\d{3}", detail_str):
                loc_str = re.sub(r"\s+", " ", detail_str).strip()
        if not loc_str or "5550" in loc_str:
            return self.location
        return {"name": "", "address": loc_str}

    def _parse_links(self, response):
        links = super()._parse_links(response)
        body_links = []
        for link in response.css(".padding li a"):
            body_links.append({
                "title": link.css("*::text").extract_first(),
                "href": response.urljoin(link.attrib["href"]),
            })
        return links + body_links
