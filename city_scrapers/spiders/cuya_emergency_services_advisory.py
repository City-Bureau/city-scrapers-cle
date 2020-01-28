import re

from city_scrapers_core.constants import ADVISORY_COMMITTEE, COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaEmergencyServicesAdvisorySpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_emergency_services_advisory"
    agency = "Cuyahoga County Emergency Services Advisory Board"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/CC-EmergencySrvcsAdvsryBrd.aspx"]

    def _parse_title(self, response):
        title_str = " ".join([
            w.strip()
            for w in response.css("#contentColumn h1::text").extract_first().strip().split(" - ")
            if "cancel" not in w.lower()
        ])
        return title_str.replace(" Meeting", "").strip()

    def _parse_classification(self, title):
        if "Committee" in title:
            return COMMITTEE
        return ADVISORY_COMMITTEE

    def _parse_location(self, response):
        loc_str = super()._parse_location(response) or ""
        split_loc = re.split(r"[-, ]{1,2}(?=\d{2})", loc_str, 1)
        loc_name = ""
        if len(split_loc) > 1:
            loc_name = split_loc[0]
            loc_addr = " ".join(split_loc[1:]).replace("Ohio", "OH")
        else:
            loc_addr = loc_str.replace("Ohio", "OH")
        if "OH" not in loc_addr:
            if "Independence" not in loc_addr:
                loc_addr += " Cleveland, OH"
            else:
                loc_addr += ", OH"
        return {
            "name": loc_name,
            "address": loc_addr.strip(),
        }
