import re
from collections import defaultdict
from datetime import datetime, time
from io import BytesIO, StringIO

import scrapy
from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


class CuyaHealthSpider(CityScrapersSpider):
    name = "cuya_health"
    agency = "Cuyahoga County Board of Health"
    timezone = "America/Detroit"
    start_urls = ["https://www.ccbh.net/board-minutes-agenda/"]
    location = {
        "name": "Cuyahoga County Board of Health",
        "address": "5550 Venture Dr, Parma, OH 44130",
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Connect to spider_idle signal and setup link_date_map for organizing links"""
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.link_date_map = defaultdict(list)
        crawler.signals.connect(spider.spider_idle, signal=scrapy.signals.spider_idle)
        return spider

    def spider_idle(self):
        """When the spider_idle signal is triggered, yield all scraped items"""
        self.crawler.signals.disconnect(self.spider_idle, signal=scrapy.signals.spider_idle)
        self.crawler.engine.crawl(
            scrapy.Request(self.start_urls[0], callback=self._yield_meetings), self
        )
        raise scrapy.exceptions.DontCloseSpider

    def parse(self, response):
        # Iterate through the first two year columns of meetings
        for link in response.css(".articleContent > div > div")[:2].css("a"):
            if ".pdf" in link.attrib["href"]:
                yield response.follow(link.attrib["href"], callback=self._parse_pdf)

    def _parse_pdf(self, response):
        lp = LAParams(line_margin=5.0)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = re.sub(r"\s+", " ", out_str.getvalue()).strip()
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", pdf_text)
        if not date_match:
            return
        date_obj = datetime.strptime(date_match.group().replace(",", ""), "%B %d %Y").date()
        self.link_date_map[date_obj].append({
            "title": "Agenda" if "agenda" in response.url.lower() else "Minutes",
            "href": response.url,
        })

    def _yield_meetings(self, response):
        for start_date, links in self.link_date_map.items():
            meeting = Meeting(
                title="Board of Health",
                description="",
                classification=BOARD,
                start=datetime.combine(start_date, time(9)),
                end=None,
                all_day=False,
                time_notes="Confirm details with agency",
                location=self.location,
                links=links,
                source=self.start_urls[0],
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting
