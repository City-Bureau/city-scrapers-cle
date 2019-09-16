import re

from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins.cuya_county import CuyaCountyMixin


class CuyaBoardRevisionSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_board_revision"
    agency = "Cuyahoga County Board of Revision"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Board-of-Revision.aspx"]
    classification = BOARD
    location = {
        "name": "County Headquarters, Room 2-101(G)",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def _parse_title(self, response):
        title_str = super()._parse_title(response)
        return title_str.replace("BOR", "Board of Revision")

    def _parse_location(self, response):
        detail_strs = response.css("blockquote dd::text").extract()
        loc_str = None
        for detail_str in detail_strs:
            if re.search(r" \d{3}", detail_str):
                loc_str = detail_str.strip()
        room_match = re.search(r"(room|rm)\.? [a-z0-9\-\(\)]+", loc_str or "", flags=re.I)
        if not loc_str or "2-101" in loc_str or not room_match:
            return self.location
        room_str = room_match.group().strip()

        # Add conference room info to location name
        return {**self.location, "name": self.location["name"].replace("Room 2-101(G)", room_str)}
