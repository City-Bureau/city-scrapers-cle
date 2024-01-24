from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaTechnicalAdvisoryCommitteeSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_technical_advisory_committee"
    agency = "Cuyahoga County Technical Advisory Committee"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/technical-advisory-committee"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
