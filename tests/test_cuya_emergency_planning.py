from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_emergency_planning import CuyaEmergencyPlanningSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_planning.html"),
    url="http://lepc.cuyahogacounty.us/en-US/meeting-schedule.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_emergency_planning_detail.html"),
    url="http://lepc.cuyahogacounty.us/en-US/070819-LEPC.aspx",
)
spider = CuyaEmergencyPlanningSpider()

freezer = freeze_time("2019-09-17")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_item["title"] == "Local Emergency Planning Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 7, 8, 13, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 7, 8, 15, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_emergency_planning/201907081330/x/local_emergency_planning_committee"
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert (
        parsed_item["source"] == "http://lepc.cuyahogacounty.us/en-US/070819-LEPC.aspx"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://lepc.cuyahogacounty.us/ViewFile.aspx?file=t5OawJ4TcSC6kSoARh5d9g%3d%3d",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
