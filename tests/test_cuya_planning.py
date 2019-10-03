from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_planning import CuyaPlanningSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_planning.html"),
    url="https://www.countyplanning.us/about/meetings/",
)
spider = CuyaPlanningSpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 11


def test_title():
    assert parsed_items[0]["title"] == "Planning Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 6, 13, 14, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cuya_planning/201906131400/x/planning_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "https://www.countyplanning.us/about/meetings/june-13-2019-meeting-agenda/",
        "title": "Agenda"
    }, {
        "href": "https://www.countyplanning.us/about/meetings/june-13-2019-meeting-minutes/",
        "title": "Minutes"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
