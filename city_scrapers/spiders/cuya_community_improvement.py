from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaCommunityImprovementSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_community_improvement"
    agency = "Cuyahoga County Community Improvement Corporation"
    start_urls = [
        "http://bc.cuyahogacounty.us/en-US/Community-Improvement-Corporation.aspx"
    ]
    classification = BOARD
    location = {
        "name": "County Headquarters, Room 407",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def _parse_start_end(self, response):
        start, end = super()._parse_start_end(response)
        if end and (end - start).days >= 1:
            end = datetime.combine(start.date(), end.time())
        return start, end

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if "407" in loc_str:
            return self.location
        return {**self.location, "address": loc_str}
