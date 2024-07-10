from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_elections import CuyaElectionsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_elections.html"),
    url="https://boe.cuyahogacounty.gov/calendar?pageSize=96&it=Current+Events",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_elections_detail.html"),
    url="https://boe.cuyahogacounty.gov/calendar/event-details/2024/07/25/default-calendar/board-meeting",  # noqa
)
spider = CuyaElectionsSpider()

freezer = freeze_time("2024-04-28")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = next(spider._parse_detail(test_detail_response))
freezer.stop()


def test_count():
    assert len(parsed_items) == 9


def test_title():
    assert parsed_item["title"] == "Board Meeting"


def test_description():
    assert parsed_item["description"] == "July Board Meeting"


def test_start():
    assert parsed_item["start"] == datetime(2024, 7, 25, 9, 30)


def test_end():
    assert parsed_item["end"] == datetime(2024, 7, 25, 10, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_elections/202407250930/x/board_meeting"


def test_status():
    assert parsed_item["status"] == "tentative"


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2925 Euclid Ave Cleveland",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://boe.cuyahogacounty.gov/calendar/event-details/2024/07/25/default-calendar/board-meeting"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://boe.cuyahogacounty.gov/about-us/board-meeting-documents",  # noqa
            "title": "Board meeting documents",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert not parsed_item["all_day"]
