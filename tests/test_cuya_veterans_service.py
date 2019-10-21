from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_veterans_service import CuyaVeteransServiceSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_veterans_service.html"),
    url="http://cuyahogavets.org/board-minutes/",
)
spider = CuyaVeteransServiceSpider()

freezer = freeze_time("2019-10-21")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 41


def test_title():
    assert parsed_items[0]["title"] == "Veterans Service Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 2, 9, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"
                           ] == "cuya_veterans_service/201901020930/x/veterans_service_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "http://cuyahogavets.org/wp-content/uploads/2019/02/Minutes0122019-002.pdf",
        "title": "Minutes",
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
