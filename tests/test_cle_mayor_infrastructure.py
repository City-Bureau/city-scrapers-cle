from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_mayor_infrastructure import CleMayorInfrastructureSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_mayor_infrastructure.html"),
    url="http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules",  # noqa
)
spider = CleMayorInfrastructureSpider()

freezer = freeze_time("2020-08-28")
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
    assert parsed_items[0]["start"] == datetime(2020, 1, 7, 14, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cle_mayor_infrastructure/202001071400/x/advisory_committee"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
