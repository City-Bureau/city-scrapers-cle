from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_children_family_advisory import (
    CuyaChildrenFamilyAdvisorySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_children_family_advisory.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/children-and-family-services-planning-committee",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_children_family_advisory_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/06/07/boards-and-commissions/060723dcfsadvisoryboard_a01bf9a3-a56e-4d64-93af-58a7c46fd1d6",  # noqa
)
spider = CuyaChildrenFamilyAdvisorySpider()

freezer = freeze_time("2024-01-20")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 6


def test_title():
    assert parsed_item["title"] == "06/07/23 DCFS Advisory Board"


def test_description():
    assert (
        parsed_item["description"]
        == "Join the Teams meeting . Meeting ID: 227 002 759 696 Passcode: xw4Pza"
    )


def test_start():
    assert parsed_item["start"] == datetime(2023, 6, 7, 18, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_children_family_advisory/202306071800/x/06_07_23_dcfs_advisory_board"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "MS Teams Meeting",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/06/07/boards-and-commissions/060723dcfsadvisoryboard_a01bf9a3-a56e-4d64-93af-58a7c46fd1d6"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/cfs/2023/060723-cfsagenda.pdf?sfvrsn=f168e538_1",  # noqa
            "title": "Agenda",
        },
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/cfs/2023/060723-cfsminutes.pdf?sfvrsn=560614ef_1",  # noqa
            "title": "Minutes",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
