from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaArchivesAdvisorySpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_archives_advisory"
    agency = "Cuyahoga County Archives Advisory Commission"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Archives-Advisory-Commission.aspx"]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "Cuyahoga County Archives Building, 3rd Floor",
        "address": "3951 Perkins Ave Cleveland, OH 44114",
    }

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if "Perkins" in loc_str:
            return self.location
        return {"name": "", "address": loc_str}
