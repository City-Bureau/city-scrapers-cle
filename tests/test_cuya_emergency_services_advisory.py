from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_emergency_services_advisory import (
    CuyaEmergencyServicesAdvisorySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_services_advisory.html"),
    url="http://bc.cuyahogacounty.us/en-US/CC-EmergencySrvcsAdvsryBrd.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_services_advisory_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/091119-CCESAB-Comms-meeting.aspx",
)
spider = CuyaEmergencyServicesAdvisorySpider()

freezer = freeze_time("2019-09-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 30


def test_title():
    assert parsed_item["title"] == "CCESAB Communications Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 11, 10, 15)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 11, 11, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_emergency_services_advisory/201909111015/x/ccesab_communications_committee"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "The Cassidy Theatre",
        "address": "6200 Pearl Road Parma Heights, OH 44130",
    }


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=7DSCAKoM0rqkeTzD%2f6%2f4cw%3d%3d",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
