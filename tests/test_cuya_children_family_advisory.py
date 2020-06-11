from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_children_family_advisory import (
    CuyaChildrenFamilyAdvisorySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_children_family_advisory.html"),
    url="http://bc.cuyahogacounty.us/en-US/Children-Family-Services-Advisory-Board.aspx",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_children_family_advisory_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/040319-DCFS-Advisory-Board.aspx",
)
spider = CuyaChildrenFamilyAdvisorySpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_item["title"] == "DCFS Advisory Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 4, 3, 16, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 4, 3, 18, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_children_family_advisory/201904031600/x/dcfs_advisory_board"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "3955 Euclid Avenue, Room #348E Cleveland, OH",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "http://bc.cuyahogacounty.us/en-US/040319-DCFS-Advisory-Board.aspx"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=YICdz%2bxQNqQfQk8n9mX1vA%3d%3d",  # noqa
            "title": "Minutes",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
