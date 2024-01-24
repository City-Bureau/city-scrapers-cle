from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_emergency_services_advisory import (
    CuyaEmergencyServicesAdvisorySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_services_advisory.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/other/emergency-services-advisory-board",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_services_advisory_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/09/ccesab-calendar/01-09-24---ccesab-emergency-management-committee",  # noqa
)
spider = CuyaEmergencyServicesAdvisorySpider()

freezer = freeze_time("2024-01-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 14


def test_title():
    assert parsed_item["title"] == "01/09/24 - CCESAB Emergency Management Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 9, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 1, 9, 10, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_emergency_services_advisory/202401090900/x/01_09_24_ccesab_emergency_management_committee"  # noqa
    )  # noqa


def test_status():
    assert parsed_item["status"] == "passed"


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "4747 East 49th Street, Cleveland, OH",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/09/ccesab-calendar/01-09-24---ccesab-emergency-management-committee"  # noqa
    )  # noqa


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/other/ccesab/em/2024/010924-emagenda.pdf?sfvrsn=9a071cac_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
