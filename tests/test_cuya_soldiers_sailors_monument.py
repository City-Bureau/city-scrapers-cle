from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_soldiers_sailors_monument import CuyaSoldiersSailorsMonumentSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_soldiers_sailors_monument.html"),
    url="http://www.soldiersandsailors.com/meeting.htm",
)
spider = CuyaSoldiersSailorsMonumentSpider()

freezer = freeze_time("2019-10-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_items[0]["title"] == "Names on the Wall Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 10, 7, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"] == "cuya_soldiers_sailors_monument/201910070900/x/names_on_the_wall_committee"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "",
        "address": "16600 Sprague Road, Middleburg Heights, OH 44130"
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
