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

freezer = freeze_time("2021-11-18")
freezer.start()
parsed_items = [item for item in spider.parse(test_response)]
freezer.stop()


def test_count():
    assert len(parsed_items) == 23


def test_title():
    assert parsed_items[0]["title"] == "Landmarks Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2021, 1, 14, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cle_landmarks/202101140900/x/landmarks_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://planning.clevelandohio.gov/landmark/agenda/2021/PDF/CLC-1-14-2021-AGENDA.pdf",  # noqa
            "title": "Agenda January 14",
        },
        {
            "href": "https://planning.clevelandohio.gov/landmark/agenda/2021/PDF/Landmarks-01-14-2021.pdf",  # noqa
            "title": "Presentation January 14"
        },
    ]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
