from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaTechnicalAdvisoryCommitteeSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_technical_advisory_committee"
    agency = "Cuyahoga County Technical Advisory Committee"
    start_urls = ["http://bc.cuyahogacounty.us/en-US/technical-advisory-committee.aspx"]
    classification = ADVISORY_COMMITTEE
    location = {
        "name": "County Headquarters",
        "address": "2079 East 9th Street, Room 4-407B, Cleveland, OH 44115",
    }

    def _parse_title(self, response):
        title_parts = (
            response.css("#contentColumn h1::text").extract_first().strip().split(" - ")
        )
        title_str = [t for t in title_parts if "cancel" not in t.lower()][0]
        return title_str.replace(" Meeting", "").strip()

    def _parse_location(self, response):
        loc_str = super()._parse_location(response)
        if self.location["address"] == loc_str:
            return self.location
        return {**self.location, "address": loc_str}

    def _parse_status(self, response, meeting):
        return self._get_status(
            meeting, text=response.css("#contentColumn h1::text").extract_first()
        )
