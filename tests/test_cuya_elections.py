from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_elections import CuyaElectionsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_elections.html"),
    url="https://boe.cuyahogacounty.gov/calendar/event-details/2024/01/23/default-calendar/board-meeting-2024-01-23",  # noqa
)
spider = CuyaElectionsSpider()

freezer = freeze_time("2022-04-28")
freezer.start()

parsed_items = [item for item in spider._parse_detail(test_response)]

freezer.stop()


def test_title():
    print(parsed_items[0]["title"])
    assert parsed_items[0]["title"] == "Board Meeting"


def test_description():
    assert (
        parsed_items[0]["description"]
        == "Certification of remaining issues, charter amendments, and write-in candidates for the\nMarch 19, 2024 Primary Election"
    )


def test_start():
    assert parsed_items[0]["start"] == datetime(2024, 1, 23, 9, 30)


def test_end():
    assert parsed_items[0]["end"] == datetime(2024, 1, 23, 10, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cuya_elections/202401230930/x/board_meeting"


def test_status():
    assert parsed_items[0]["status"] == "tentative"


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "",
        "address": "2925 Euclid Ave\nCleveland",
    }


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://boe.cuyahogacounty.gov/calendar/event-details/2024/01/23/default-calendar/board-meeting-2024-01-23"  # noqa
    )


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://boe.cuyahogacounty.gov/about-us/board-meeting-documents",
            "title": "Board meeting documents",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
