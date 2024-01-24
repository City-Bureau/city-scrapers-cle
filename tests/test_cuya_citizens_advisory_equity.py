from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_citizens_advisory_equity import (
    CuyaCitizensAdvisoryEquitySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_citizens_advisory_equity.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/citizens-advisory-council-on-equity",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_citizens_advisory_equity_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/11/boards-and-commissions/121123-cace-meeting",  # noqa
)
spider = CuyaCitizensAdvisoryEquitySpider()

freezer = freeze_time("2021-01-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


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
    )


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
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/wdb/2023/111723-ccwdbagenda.pdf?sfvrsn=740b923b_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
