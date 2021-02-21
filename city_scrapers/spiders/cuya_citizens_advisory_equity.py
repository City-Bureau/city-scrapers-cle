from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaCitizensAdvisoryEquitySpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_citizens_advisory_equity"
    agency = "Cuyahoga County Citizens' Advisory Council on Equity"
    start_urls = [
        "http://bc.cuyahogacounty.us/en-US/Citizens-Advisory-Council-Equity.aspx"
    ]
    classification = ADVISORY_COMMITTEE

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if loc_str is None:
            return {"name": "Remote", "address": ""}
        return {"name": "", "address": loc_str}
