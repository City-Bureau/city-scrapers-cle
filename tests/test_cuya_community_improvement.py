from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_community_improvement import (
    CuyaCommunityImprovementSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_community_improvement.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/community-improvement-corporation",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_community_improvement_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/14/boards-and-commissions/12-14-2023---cuyahoga-county-community-improvement-corporation-meeting",  # noqa
)
spider = CuyaCommunityImprovementSpider()

freezer = freeze_time("2024-01-21")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 10


def test_title():
    assert (
        parsed_item["title"]
        == "12/14/2023 - Cuyahoga County Community Improvement Corporation Meeting"
    )


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 12, 14, 8, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 12, 14, 9, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_community_improvement/202312140800/x/12_14_2023_cuyahoga_county_community_improvement_corporation_meeting"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 East Ninth Street Room 4-407",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/14/boards-and-commissions/12-14-2023---cuyahoga-county-community-improvement-corporation-meeting"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/cccic/2023/121423-cccicagenda.pdf?sfvrsn=fee5de43_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
