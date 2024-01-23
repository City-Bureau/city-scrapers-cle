import datetime
from typing import Any

import dateutil.parser
from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy.http import Response

from city_scrapers.mixins import CuyaCountyMixin2


class CuyaChildrenFamilyAdvisorySpider(CuyaCountyMixin2, CityScrapersSpider):
    name = "cuya_children_family_advisory"
    agency = "Cuyahoga County Children and Family Services Advisory Board"
    start_urls = [
        "https://cuyahogacounty.gov/boards-and-commissions/board-details/external/children-and-family-services-planning-committee"  # noqa
    ]
    classification = ADVISORY_COMMITTEE
