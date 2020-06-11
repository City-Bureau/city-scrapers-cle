from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaChildrenFamilyAdvisorySpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_children_family_advisory"
    agency = "Cuyahoga County Children and Family Services Advisory Board"
    start_urls = [
        "http://bc.cuyahogacounty.us/en-US/Children-Family-Services-Advisory-Board.aspx"
    ]
    classification = ADVISORY_COMMITTEE

    def _parse_location(self, response):
        detail_strs = response.css("blockquote dd::text").extract()
        loc_str = detail_strs[2].strip()
        if loc_str != "TBD" and "Cleveland" not in loc_str:
            loc_str += " Cleveland, OH"
        return {
            "name": "",
            "address": loc_str,
        }
