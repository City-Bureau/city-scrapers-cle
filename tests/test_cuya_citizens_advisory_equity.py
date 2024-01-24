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

freezer = freeze_time("2024-01-20")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_item["title"] == "12/11/23 - CACE meeting"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 12, 11, 15, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 12, 11, 17, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_citizens_advisory_equity/202312111500/x/12_11_23_cace_meeting"
    )  # noqa


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 East 9th Street Room 5-006, Cleveland, Ohio 44113",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/11/boards-and-commissions/121123-cace-meeting"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/cace/2023/121123-caceagenda.pdf?sfvrsn=902f11f4_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
