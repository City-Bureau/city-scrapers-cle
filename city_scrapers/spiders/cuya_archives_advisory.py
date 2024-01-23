from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaArchivesAdvisorySpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_archives_advisory"
    agency = "Cuyahoga County Archives Advisory Commission"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/archives-advisory-commission"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
