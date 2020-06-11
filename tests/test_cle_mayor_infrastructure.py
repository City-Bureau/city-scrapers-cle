from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_mayor_infrastructure import CleMayorInfrastructureSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_mayor_infrastructure.html"),
    url="http://planning.city.cleveland.oh.us/designreview/schedule.php",
)
spider = CleMayorInfrastructureSpider()

freezer = freeze_time("2019-09-11")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_tests():
    assert len(parsed_items) == 24


def test_title():
    assert parsed_items[0]["title"] == "Advisory Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 2, 14, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cle_mayor_infrastructure/201901021400/x/advisory_committee"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }


def test_source():
    assert (
        parsed_items[0]["source"]
        == "http://planning.city.cleveland.oh.us/designreview/schedule.php"
    )


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
