from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_regional_data_sharing import (
    CuyaRegionalDataSharingSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_regional_data_sharing.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/other/regional-data-enterprise-sharing-system",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_regional_data_sharing_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/10/19/boards-and-commissions/redss-board-meeting---10-19-23",  # noqa
)
spider = CuyaRegionalDataSharingSpider()

freezer = freeze_time("2024-1-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_item["title"] == "REDSS Board Meeting - 10/19/23"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 10, 19, 13, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 10, 19, 14, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_regional_data_sharing/202310191300/x/redss_board_meeting_10_19_23"  # noqa
    )


def test_status():
    assert parsed_item["status"] == "passed"


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 East 9th St. Cleveland, OH 44115 - Room 4-407",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/10/19/boards-and-commissions/redss-board-meeting---10-19-23"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/agendas/101923-redssmeetingmin.pdf?sfvrsn=5aa73ec9_1",  # noqa
            "title": "Minutes",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == "Board"


def test_all_day():
    assert parsed_item["all_day"] is False
