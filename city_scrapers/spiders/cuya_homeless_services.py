from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaHomelessServicesSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_homeless_services"
    agency = "Cuyahoga County Office of Homeless Services Advisory Board"
    start_urls = ["http://ohs.cuyahogacounty.us/en-US/Advisory-Board.aspx"]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "",
        "address": "2012 W 25th St, 6th Floor, Cleveland, OH 44113",
    }

    def parse(self, response):
        for detail_link in response.css("#rightColumn td:nth-child(2) a::attr(href)").extract():
            yield response.follow(detail_link, callback=self._parse_detail, dont_filter=True)

    def _parse_title(self, response):
        title_str = response.css("#rightColumn h1::text").extract_first().strip()
        if "Special" in title_str:
            return title_str
        return title_str.replace(" Meeting", "").strip()

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if "2012" in loc_str:
            return self.location
        return {"name": "", "address": loc_str}
