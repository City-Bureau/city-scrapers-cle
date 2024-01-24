from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaEmergencyServicesAdvisorySpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_emergency_services_advisory"
    agency = "Cuyahoga County Emergency Services Advisory Board"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/other/emergency-services-advisory-board"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
