from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, FORUM, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_reentry_leadership import CuyaReentryLeadershipSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_reentry_leadership.html"),
    url="http://reentry.cuyahogacounty.us/en-US/Leadership-Coalition.aspx",
)
spider = CuyaReentryLeadershipSpider()

freezer = freeze_time("2019-10-04")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_items[0]["title"] == "Leadership Coalition"
    assert parsed_items[-1]["title"] == "Asset Mapping & Community Wide Update Announcements"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 18, 10, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 1, 18, 11, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cuya_reentry_leadership/201901181000/x/leadership_coalition"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "ADAMHS Board",
        "address": "2012 West 25th Street Cuyahoga Room, 6th Floor Cleveland, OH 44103",
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION
    assert parsed_items[-1]["classification"] == FORUM


def test_all_day():
    assert parsed_items[0]["all_day"] is False
