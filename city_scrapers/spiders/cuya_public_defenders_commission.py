from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaPublicDefendersCommissionSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_public_defenders_commission"
    agency = "Cuyahoga County Public Defenders Commission"
    start_urls = ["http://publicdefender.cuyahogacounty.us/en-US/Event_calendar.aspx"]
    location = {
        "name": "Courthouse Square",
        "address": "310 Lakeside Ave, Suite 400, Cleveland, OH 44113",
    }
    classification = COMMISSION

    def parse(self, response):
        for detail_link in response.css(".SearchResults td:nth-child(2) a::attr(href)").extract():
            yield response.follow(detail_link, callback=self._parse_detail, dont_filter=True)

    def _parse_title(self, response):
        return "Public Defenders Commission"

    def _parse_location(self, response):
        return self.location
