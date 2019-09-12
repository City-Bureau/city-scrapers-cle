from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_transit_community_advisory import CleTransitCommunityAdvisorySpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_transit_community_advisory.html"),
    url="http://www.riderta.com/CAC",
)
spider = CleTransitCommunityAdvisorySpider()

freezer = freeze_time("2019-09-12")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 23


def test_title():
    assert parsed_items[0]["title"] == "Transit Improvement Advisory Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 2, 14, 8, 30)


def test_end():
    assert parsed_items[0]["end"] == datetime(2019, 2, 14, 10, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"
    ] == "cle_transit_community_advisory/201902140830/x/transit_improvement_advisory_committee"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "RTA Main Office, Meeting Room 1",
        "address": "1240 W 6th St Cleveland, OH 44113"
    }


def test_source():
    assert parsed_items[0]["source"] == "http://www.riderta.com/CAC"


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
