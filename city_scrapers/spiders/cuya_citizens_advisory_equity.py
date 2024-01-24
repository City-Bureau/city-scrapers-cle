from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaCitizensAdvisoryEquitySpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_citizens_advisory_equity"
    agency = "Cuyahoga County Citizens' Advisory Council on Equity"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/citizens-advisory-council-on-equity"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
