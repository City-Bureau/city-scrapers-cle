from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaBudgetCommissionSpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_budget_commission"
    agency = "Cuyahoga County Budget Commission"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/budget-commission"  # noqa
    ]
    classification = COMMISSION
