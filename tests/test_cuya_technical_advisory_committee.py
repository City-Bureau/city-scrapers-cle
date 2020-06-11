from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, CANCELLED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_technical_advisory_committee import (
    CuyaTechnicalAdvisoryCommitteeSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_technical_advisory_committee.html"),
    url="http://bc.cuyahogacounty.us/en-US/technical-advisory-committee.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_technical_advisory_committee_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/TACMeeting-082919.aspx",
)
spider = CuyaTechnicalAdvisoryCommitteeSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 21


def test_title():
    assert parsed_item["title"] == "Technical Advisory Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 8, 29, 9, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 8, 29, 10, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_technical_advisory_committee/201908290930/x/technical_advisory_committee"  # noqa
    )


def test_status():
    assert parsed_item["status"] == CANCELLED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert (
        parsed_item["source"]
        == "http://bc.cuyahogacounty.us/en-US/TACMeeting-082919.aspx"
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
