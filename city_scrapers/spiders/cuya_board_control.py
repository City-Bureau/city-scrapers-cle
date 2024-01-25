from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaBoardControlSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_board_control"
    agency = "Cuyahoga County Board of Control"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/board-of-control"  # noqa
    ]
    classification = BOARD
