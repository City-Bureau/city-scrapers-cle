from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_landmarks import CleLandmarksSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_landmarks.html"),
    url=CleLandmarksSpider.start_urls[0],
)
spider = CleLandmarksSpider()

freezer = freeze_time("2020-05-20")
freezer.start()
parsed_items = [item for item in spider.parse(test_response)]
freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_items[0]["title"] == "Landmarks Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 1, 9, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cle_landmarks/202001090900/x/landmarks_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "http://clevelandohio.gov/sites/default/files/planning/landmark/agenda/2020/CLC-1-9-2020-AGENDA.pdf",  # noqa
            "title": "Agenda",
        },
        {"href": "http://clevelandohio.gov/node/164775", "title": "Photo Gallery"},
    ]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
