from datetime import datetime
from operator import itemgetter
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_building_standards import CleBuildingStandardsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_building_standards.html"),
    url="http://planning.city.cleveland.oh.us/bza/bbs.html",
)
spider = CleBuildingStandardsSpider()

freezer = freeze_time("2019-09-11")
freezer.start()

parsed_items = sorted(
    [item for item in spider.parse(test_response)], key=itemgetter("start")
)

freezer.stop()


def test_count():
    assert len(parsed_items) == 18


def test_title():
    assert (
        parsed_items[0]["title"] == "Board of Building Standards and Building Appeals"
    )


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 23, 9, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cle_building_standards/201901230930/x/board_of_building_standards_and_building_appeals"  # noqa
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert (
        parsed_items[0]["source"] == "http://planning.city.cleveland.oh.us/bza/bbs.html"
    )


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "http://planning.city.cleveland.oh.us/bza/bbs/agenda/2019/AGENDA01232019.pdf",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
