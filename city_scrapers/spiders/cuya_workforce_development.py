from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaWorkforceDevelopmentSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_workforce_development"
    agency = "Cleveland/Cuyahoga County Workforce Development Board"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/cleveland-cuyahoga-county-workforce-development-board"  # noqa
    ]
    classification = BOARD
