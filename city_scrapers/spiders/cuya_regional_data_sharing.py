from city_scrapers_core.constants import BOARD
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaRegionalDataSharingSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_regional_data_sharing"
    agency = "Cuyahoga County Regional Enterprise Data Sharing System"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/other/regional-data-enterprise-sharing-system"  # noqa
    ]
    classification = BOARD
