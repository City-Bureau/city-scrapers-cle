from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_transformation_alliance import CleTransformationAllianceSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_transformation_alliance.html"),
    url="https://mycleschool.org/category/events/board-of-directors-events/",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cle_transformation_alliance_detail.html"),
    url="https://mycleschool.org/transformation-alliance-finance-committee-meeting/",
)
spider = CleTransformationAllianceSpider()

freezer = freeze_time("2019-10-05")
freezer.start()

parsed_items = [item for item in spider._parse_events(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 10


def test_title():
    assert parsed_item["title"] == "Finance Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2018, 11, 27, 8, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cle_transformation_alliance/201811270830/x/finance_committee"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {"name": "", "address": "1240 Huron Rd East, Cleveland 44115"}


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
