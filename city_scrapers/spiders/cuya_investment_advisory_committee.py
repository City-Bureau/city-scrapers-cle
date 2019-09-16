import re

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaInvestmentAdvisoryCommitteeSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_investment_advisory_committee"
    agency = "Cuyahoga County Investment Advisory Committee"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Investment-Advisory-Committee.aspx"]
    classification = ADVISORY_COMMITTEE

    def _parse_title(self, response):
        return response.css("#contentColumn h1::text").extract_first().strip()

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if " room" not in loc_str.lower() and " rm" not in loc_str.lower():
            return self.location
        split_loc = re.split(r" (?=2079)", loc_str)
        return {**self.location, "address": " ".join(split_loc[1:])}
