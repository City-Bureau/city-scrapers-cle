from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_community_improvement import (
    CuyaCommunityImprovementSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_community_improvement.html"),
    url="http://bc.cuyahogacounty.us/en-US/Community-Improvement-Corporation.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_community_improvement_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/081419-CCCIC-meeting.aspx",
)
spider = CuyaCommunityImprovementSpider()

freezer = freeze_time("2019-09-21")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Cuyahoga County Community Improvement Corporation"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 8, 14, 8, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 8, 14, 9, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_community_improvement/201908140800/x/cuyahoga_county_community_improvement_corporation"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert (
        parsed_item["source"]
        == "http://bc.cuyahogacounty.us/en-US/081419-CCCIC-meeting.aspx"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=BboqmBFdco6MkRoTABFWig%3d%3d",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
