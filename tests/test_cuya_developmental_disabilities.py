from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, FORUM, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_developmental_disabilities import (
    CuyaDevelopmentalDisabilitiesSpider
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_developmental_disabilities.pdf"),
    url="http://www.cuyahogabdd.org/pdf_BDD/en-US/2019%20Bd%20Mtg%20Sched.pdf",
    mode="rb",
)
spider = CuyaDevelopmentalDisabilitiesSpider()

freezer = freeze_time("2019-10-07")
freezer.start()

parsed_items = [item for item in spider._parse_pdf(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 13


def test_title():
    assert parsed_items[0]["title"] == "Board"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 24, 17, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cuya_developmental_disabilities/201901241730/x/board"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == BOARD
    assert parsed_items[9]["classification"] == FORUM


def test_all_day():
    assert parsed_items[0]["all_day"] is False
