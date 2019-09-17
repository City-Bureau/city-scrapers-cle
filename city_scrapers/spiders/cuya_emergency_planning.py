from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaEmergencyPlanningSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_emergency_planning"
    agency = "Cuyahoga County Local Emergency Planning Committee"
    start_urls = ["http://lepc.cuyahogacounty.us/en-US/meeting-schedule.aspx"]
    classification = COMMISSION
    location = {
        "name": "NEORSD Environmental Maintenance Center",
        "address": "4747 East 49th St Cleveland, OH 44125",
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
        if "NEORSD" in loc_str:
            return self.location
        return {"name": "", "address": loc_str}
