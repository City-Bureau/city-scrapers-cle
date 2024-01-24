from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_workforce_development import (
    CuyaWorkforceDevelopmentSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_workforce_development.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/cleveland-cuyahoga-county-workforce-development-board",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_workforce_development_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/17/boards-and-commissions/wd-board-meeting-111723",  # noqa
)
spider = CuyaWorkforceDevelopmentSpider()

freezer = freeze_time("2024-01-17")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 6


def test_title():
    assert parsed_item["title"] == "Workforce Development Board Meeting - 11/17/23"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 11, 17, 8, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 11, 17, 10, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_workforce_development/202311170800/x/workforce_development_board_meeting_11_17_23"  # noqa
    )  # noqa


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "1910 Carnegie Avenue, Cleveland, OH 44115",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/17/boards-and-commissions/wd-board-meeting-111723"  # noqa
    )  # noqa


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/wdb/2023/111723-ccwdbagenda.pdf?sfvrsn=740b923b_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
