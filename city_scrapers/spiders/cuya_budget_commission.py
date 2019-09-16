from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaBudgetCommissionSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_budget_commission"
    agency = "Cuyahoga County Budget Commission"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Budget-Commission.aspx"]
    classification = COMMISSION

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        return {
            "name": "Cuyahoga County Headquarters",
            "address": loc_str,
        }
