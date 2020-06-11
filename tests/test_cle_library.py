from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_library import CleLibrarySpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_library_meetings.html"),
    url="https://cpl.org/category/meeting/",
)
test_minutes_response = file_response(
    join(dirname(__file__), "files", "cle_library.html"),
    url="https://cpl.org/category/meeting/",
)
spider = CleLibrarySpider()

freezer = freeze_time("2019-09-11")
freezer.start()

spider.minutes_map = spider._parse_minutes(test_minutes_response)
parsed_items = [item for item in spider._parse_meetings(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_items[0]["title"] == "Special Board Meeting"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 8, 29, 12, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cle_library/201908291200/x/special_board_meeting"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == "https://cpl.org/special-board-meeting-4/"


def test_links():
    assert parsed_items[0]["links"] == [
        {"href": "https://cpl.org/special-board-meeting-4/", "title": "Agenda"}
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
