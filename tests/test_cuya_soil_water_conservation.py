from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_soil_water_conservation import (  # noqa
    CuyaSoilWaterConservation,
)

# Mock the response from the list page and detail page
test_response = file_response(
    join(dirname(__file__), "files", "cuya_soil_water_conservation.html"),
    url="https://cuyahogaswcd.org/events/?category_filter%5B%5D=1",
)
test_detail_response = file_response(
    join(
        dirname(__file__), "files", "cuya_soil_water_conservation_detail.html"
    ),  # noqa
    url="https://cuyahogaswcd.org/events/cuyahoga-swcd-board-meeting-5/",
)

# Initialize the spider
spider = CuyaSoilWaterConservation()

# Freeze time to ensure consistent test results
freezer = freeze_time("2024-07-30")
freezer.start()

# Parse items using the spider
parsed_items = [item for item in spider.parse(test_response)]
parsed_item = next(spider._parse_meeting(test_detail_response))

freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "Cuyahoga SWCD August Board Meeting"


def test_description():
    assert parsed_item["description"] == (
        "Cuyahoga SWCD office\n3311 Perkins Avenue, Suite 100\nCleveland, Ohio 44114\n\n"  # noqa
        "The public is welcome to attend.\n\n"
        "To obtain a copy of the agenda and login information, members of the public may "  # noqa
        "register to participate in the meeting by using Contact Us below, or by calling "  # noqa
        "the District office at 216/524-6580, ext. 1000.\n\n"
        "The member of the public must be connected to the board meeting via the internet, "  # noqa
        "telephone or in person when the Board Chair recognizes visitors."
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 8, 26, 18, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_soil_water_conservation/202408261830/x/cuyahoga_swcd_august_board_meeting"  # noqa
    )


def test_location():
    assert parsed_item["location"] == {
        "name": "Cuyahoga SWCD office",
        "address": "3311 Perkins Ave, Suite 100, Cleveland, OH 44114",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogaswcd.org/events/cuyahoga-swcd-board-meeting-5/"
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False


def test_status():
    assert parsed_item["status"] == "tentative"
