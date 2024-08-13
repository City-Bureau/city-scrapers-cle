from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin


class CuyaPersonnelReviewCommissionSpider(CuyaCountyMixin, CityScrapersSpider):
    name = "cuya_personnel_review_commission"
    agency = "Cuyahoga County Personnel Review Commission"
    start_urls = ["https://prc.cuyahogacounty.us/en-US/PRC-Meetings-Resolutions.aspx"]
    classification = COMMISSION

    def parse(self, response):
        # Pull the most recent 12 meetings
        for detail_link in response.css(
            "#contentColumn td:nth-child(3) a::attr(href)"
        ).extract()[:12]:
            # Ignore links to the live-stream for parsing
            if detail_link.endswith("Streaming-Video.aspx"):
                continue
            yield response.follow(
                detail_link, callback=self._parse_detail, dont_filter=True
            )

    def _parse_title(self, response):
        title_parts = (
            response.css("#contentColumn h1::text").extract_first().strip().split(" - ")
        )
        title_str = [t for t in title_parts if "cancel" not in t.lower()][0]
        if "Special" in title_str:
            return title_str
        return title_str.replace(" Meeting", "").strip()

    def _parse_location(self, response):
        return {
            "name": "",
            "address": super()._parse_location(response),
        }

    def _parse_status(self, response, meeting):
        return self._get_status(
            meeting, text=response.css("#contentColumn h1::text").extract_first()
        )
