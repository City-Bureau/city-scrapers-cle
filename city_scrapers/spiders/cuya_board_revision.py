from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaBoardRevisionSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_board_revision"
    agency = "Cuyahoga County Board of Revision"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/board-of-revision"  # noqa
    ]
    classification = BOARD
