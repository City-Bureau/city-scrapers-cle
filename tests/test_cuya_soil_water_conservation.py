from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_soil_water_conservation import CuyaSoilWaterConservation

test_response = file_response(
    join(dirname(__file__), "files", "cuya_soil_water_conservation.html"),
    url="https://www.cuyahogaswcd.org/events/2019/09/23/cuyahoga-swcd-board-meeting",
)
spider = CuyaSoilWaterConservation()

freezer = freeze_time("2019-09-13")
freezer.start()

parsed_item = [item for item in spider._parse_meeting(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board of Supervisors"


def test_description():
    assert (
        parsed_item["description"]
        == """Meets fourth Monday of each month at Cuyahoga SWCD offices at 6:30pm with the exception of January, February, May and December. All meeting are open to the public.
January 29 (Tuesday)
February 19 (Tuesday)
March 25
April 22
May 20 (Monday)
June 24
July 22
August 26
September 23
October 28
November 25
December 16 (Monday)
Members of the media or general public that would like to be notified of SWCD special meetings or meetings of a special topic may notify the District at 216/524-6580.
Click
here
for more information on our Board of Supervisors"""  # noqa
    )


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 23, 18, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 23, 20, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_soil_water_conservation/201909231830/x/board_of_supervisors"
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "Cuyahoga SWCD office",
        "address": "3311 Perkins Ave Suite 100 Cleveland, OH 44114",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.cuyahogaswcd.org/events/2019/09/23/cuyahoga-swcd-board-meeting"
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
