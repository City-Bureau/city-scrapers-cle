import re

from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaWorkforceDevelopmentSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_workforce_development"
    agency = "Cleveland/Cuyahoga County Workforce Development Board"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Workforce-Development.aspx"]
    classification = BOARD

    def _parse_title(self, response):
        title_parts = response.css("#contentColumn h1::text"
                                   ).extract_first().strip().split("Development ")
        return title_parts[-1].strip()

    def _parse_description(self, response):
        return re.sub(
            r"\s+", " ",
            " ".join(response.css("#contentColumn .padding > div > p *::text").extract())
        ).strip()

    def _parse_location(self, response):
        address = super()._parse_location(response)
        if address:
            address = address.replace(", Ohio", ", OH")
        else:
            address = ""
        return {"name": "", "address": address}
