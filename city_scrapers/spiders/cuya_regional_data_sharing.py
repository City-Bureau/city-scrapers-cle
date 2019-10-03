import re

from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaRegionalDataSharingSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_regional_data_sharing"
    agency = "Cuyahoga County Regional Enterprise Data Sharing System"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/CRIS.aspx"]
    classification = BOARD
    location = {
        "name": "County Headquarters, 5th Floor Rm. 5-006",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def _parse_title(self, response):
        return "Governing Board"

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if "5-006" in loc_str:
            return self.location
        split_loc = re.split(r" (?=2079)", loc_str)
        return {"name": "", "address": " ".join(split_loc[1:])}
