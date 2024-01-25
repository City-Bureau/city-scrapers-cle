from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaAuditSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_audit"
    agency = "Cuyahoga County Audit Committee"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/audit-committee"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "County Headquarters, 4-407 Conference Room B",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }
