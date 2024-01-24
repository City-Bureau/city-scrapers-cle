from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaInvestmentAdvisoryCommitteeSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_investment_advisory_committee"
    agency = "Cuyahoga County Investment Advisory Committee"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/investment-advisory-committee"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
