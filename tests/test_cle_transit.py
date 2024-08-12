from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_transit import CleTransitSpider

test_response_meetings = file_response(
    join(dirname(__file__), "files", "cle_transit.html"),
    url="https://www.riderta.com/board",
)
test_response_meeting = file_response(
    join(dirname(__file__), "files", "cle_transit_meeting.html"),
    url="https://www.riderta.com/events/2024/7/30/board-meeting",
)
spider = CleTransitSpider()

freezer = freeze_time("2024-09-12")
freezer.start()

parsed_items = [item for item in spider._parse(test_response_meetings)]
parsed_item = next(spider._parse_meeting(test_response_meeting))

freezer.stop()


def test_count():
    assert len(parsed_items) == 37


def test_title():
    assert parsed_item["title"] == "Board Meeting"


def test_description():
    assert parsed_item["description"] == (
        "The RTA Board of Trustees will meet at 9 a.m. July 30, 2024 in the Main Office "  # noqa
        "Board Room, 1240 West 6th Street, Cleveland, OH 44113. 216-356-3016, office 216-501-0242, cell"  # noqa
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 7, 30, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 7, 30, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cle_transit/202407300900/x/board_meeting"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "1240 West 6th St, Cleveland, OH 44113",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.riderta.com/events/2024/7/30/board-meeting"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://www.riderta.com/sites/default/files/events/2024-07-30Board%26CmtPackage.pdf",  # noqa
            "title": "2024-07-30Board&CmtPackage.pdf",
        },
        {
            "href": "https://www.riderta.com/sites/default/files/events/2024-07-30Presentations.pdf",  # noqa
            "title": "2024-07-30Presentations.pdf",
        },
        {
            "href": "https://www.riderta.com/sites/default/files/events/2024-07-30CompensationMinutes.pdf",  # noqa
            "title": "2024-07-30CompensationMinutes.pdf",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
