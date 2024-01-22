from typing import Any
from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy.http import Response
import dateutil.parser
import datetime
from city_scrapers.mixins import CuyaCountyMixin
from city_scrapers_core.items import Meeting


class CuyaChildrenFamilyAdvisorySpider(CityScrapersSpider):
    name = "cuya_children_family_advisory"
    agency = "Cuyahoga County Children and Family Services Advisory Board"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/children-and-family-services-planning-committee"
    ]
    classification = ADVISORY_COMMITTEE

    def parse(self, response):
        links = response.css(".row.bceventgrid > table > tbody > tr > td:nth-child(2) > a::attr(href)").extract()
        for link in links:
            yield response.follow(link, callback=self._parse_detail, dont_filter=True)
    
    def _parse_detail(self, response: Response) -> Any:
        main_el = response.css("div.moudle")
        meeting = Meeting(
            title=self._parse_title(main_el),
            description= self._parse_description(main_el),
            classification= self.classification,
            start=self._parse_start(main_el),
            end=None,
            time_notes= "",
            all_day= False,
            location= "",
            links= None,
            source= "",
        )
        yield meeting

    def _parse_title(self, response: Response) -> str:
        title_str = response.css("h1.title::text").extract_first().strip()
        return title_str
    
    def _parse_description(self, response: Response) -> str:
        texts = response.css('.content ::text').extract()
        cleaned_texts = [text.strip() for text in texts if text.strip()]
        full_text = ' '.join(cleaned_texts)
        return full_text

    def _parse_start(self, response):
        # Extract the start date from the 'content' attribute
        start_date_str = response.css('.meta-item[itemprop="startDate"] ::attr(content)').get()
        start_date = dateutil.parser.parse(start_date_str).date()

        # Extract the time text
        text_nodes = response.css(".meta-item[itemprop='startDate'] > p::text").extract()
        time_str = text_nodes[1].strip()
        start_time = dateutil.parser.parse(time_str).time()

        # Combine the start date and time to get the start datetime
        start_datetime = datetime.datetime.combine(start_date, start_time)

        return start_datetime
