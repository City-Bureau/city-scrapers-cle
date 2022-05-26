from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMITTEE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_mental_health_response import (
    CuyaMentalHealthResponseSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_mental_health_response.html"),
    url="https://www.adamhscc.org/about-us/current-initiatives/task-forces-and-coalitions/mental-health-response-advisory-committee-mhrac",  # noqa
)
spider = CuyaMentalHealthResponseSpider()

freezer = freeze_time("2022-05-17")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


"""
Uncomment below
"""


def test_title():
    assert parsed_items[0]["title"] == "MHRAC QI Subcommittee Meeting"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2022, 5, 17, 9, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2022, 5, 17, 10, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cuya_mental_health_response/202205170900/x/mhrac_qi_subcommittee_meeting"
    )


def test_status():
    assert parsed_items[0]["status"] == "tentative"


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Zoom link in meeting links.",
        "address": "",
    }


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://www.adamhscc.org/about-us/current-initiatives/task-forces-and-coalitions/mental-health-response-advisory-committee-mhrac"  # noqa
    )


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.adamhscc.org/Home/Components/Calendar/Event/854/110",  # noqa
            "title": "Meeting details",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
