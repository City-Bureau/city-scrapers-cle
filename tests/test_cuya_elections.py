from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_elections import CuyaElectionsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_elections.html"),
    url="https://boe.cuyahogacounty.us/en-US/08272019meeting.aspx",
)
spider = CuyaElectionsSpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_item = [item for item in spider._parse_detail(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board of Elections"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 8, 27, 14, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 8, 27, 15, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_elections/201908271400/x/board_of_elections"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == test_response.url


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://boe.cuyahogacounty.us/ViewFile.aspx?file=9Fsk2MKlT8E%3d",
        "title": "Board Agenda",
    }]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
