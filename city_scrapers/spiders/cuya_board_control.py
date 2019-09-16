from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins.cuya_county import CuyaCountyMixin


class CuyaBoardControlSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_board_control"
    agency = "Cuyahoga County Board of Control"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Board-of-Control.aspx"]
    classification = BOARD
