from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_gateway_economic_development import (
    CleGatewayEconomicDevelopmentSpider
)

test_response = file_response(
    join(dirname(__file__), "files", "cle_gateway_economic_development.html"),
    url="https://www.gwcomplex.org/boardmeetings.html",
)
spider = CleGatewayEconomicDevelopmentSpider()

freezer = freeze_time("2019-09-13")
freezer.start()

parsed_items = [item for item in spider._parse_meetings(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 2, 13, 15, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"
                           ] == "cle_gateway_economic_development/201902131500/x/board_of_trustees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == "https://www.gwcomplex.org/boardmeetings.html"


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "https://www.gwcomplex.org/meetings/BoardMeetingAgenda02132019.pdf",
        "title": "Agenda"
    }, {
        "href": "https://www.gwcomplex.org/meetings/BoardMinutes021319.pdf",
        "title": "Minutes"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
