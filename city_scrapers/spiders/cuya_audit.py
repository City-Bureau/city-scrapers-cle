import re

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaAuditSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_audit"
    agency = "Cuyahoga County Audit Committee"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/Audit-Committee.aspx"]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "County Headquarters, 4-407 Conference Room B",
        "address": "2079 East 9th St Cleveland, OH 44115",
    }

    def _parse_location(self, response):
        detail_strs = response.css("blockquote dd::text").extract()
        loc_str = None
        for detail_str in detail_strs:
            if re.search(r"\d{3}", detail_str):
                loc_str = re.sub(r"\s+", " ", detail_str).strip()
        if not loc_str or "2079" in loc_str:
            return self.location
        return {"name": "", "address": loc_str}
