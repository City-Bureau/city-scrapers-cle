from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_design_review import CleDesignReviewSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_design_review.html"),
    url="http://planning.city.cleveland.oh.us/designreview/schedule.php",
)
spider = CleDesignReviewSpider()

freezer = freeze_time("2019-09-09")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 163


def test_title():
    assert parsed_items[0]["title"] == "Downtown/Flats Design Review Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 3, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"] == "cle_design_review/201901030900/x/downtown_flats_design_review_committee"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }
    assert parsed_items[-1]["location"] == {
        "address": "13512 Kinsman Road Cleveland, OH",
        "name": "York-Rite Mason Temple",
    }


def test_source():
    assert parsed_items[0]["source"
                           ] == "http://planning.city.cleveland.oh.us/designreview/schedule.php"


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_items[10]["links"] == [{
        "href":
            "http://planning.city.cleveland.oh.us/designreview/drcagenda/2019/06072019/CLE-DRACagenda-6-06-19.pdf",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
