from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaCommunityImprovementSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_community_improvement"
    agency = "Cuyahoga County Community Improvement Corporation"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/community-improvement-corporation"  # noqa
    ]
    classification = BOARD
