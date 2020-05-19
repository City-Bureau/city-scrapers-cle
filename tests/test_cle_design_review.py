from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_design_review import CleDesignReviewSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_design_review.html"),
    url=(
        "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules"  # noqa
    )
)
spider = CleDesignReviewSpider()

freezer = freeze_time("2020-05-19")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 165


def test_title():
    assert parsed_items[0]["title"] == "Downtown/Flats Design Review Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 1, 2, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"] == "cle_design_review/202001020900/x/downtown_flats_design_review_committee"


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
    assert parsed_items[0][
        "source"
    ] == "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules"  # noqa


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_items[1]["links"] == [{
        'href':
            'http://clevelandohio.gov/sites/default/files/planning/drc/agenda/2020/DF-DRAC-agenda-1-16-20.pdf',  # noqa
        'title': 'Agenda'
    }]


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
