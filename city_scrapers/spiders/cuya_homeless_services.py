from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaHomelessServicesSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_homeless_services"
    agency = "Cuyahoga County Office of Homeless Services Advisory Board"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/cleveland-cuyahoga-office-of-homeless-services-advisory-board"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "Office of Health and Human Services",
        "address": "310 West Lakeside Avenue, 5th Floor, Cleveland, Ohio 44113",
    }

    def _parse_location(self, selector):
        return self.location
