from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaBoardControlSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_board_control"
    agency = "Cuyahoga County Board of Control"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Board-of-Control.aspx"]
    classification = BOARD

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if not loc_str:
            return self.location
        # Add conference room info to location name
        loc = {**self.location}
        loc_details = loc_str.split(", ")[-1]
        loc["name"] += " " + loc_details
        return loc
