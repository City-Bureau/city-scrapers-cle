from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import CITY_COUNCIL, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_county_council import CuyaCountyCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_county_council.json"),
    url="http://council.cuyahogacounty.us/api/items/GetItemsByType",
)
spider = CuyaCountyCouncilSpider()

freezer = freeze_time("2019-09-13")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 49


def test_title():
    assert parsed_items[0]["title"] == "Committee of the Whole Meeting/Executive Session"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 6, 25, 14, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"
    ] == "cuya_county_council/201906251430/x/committee_of_the_whole_meeting_executive_session"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "C. Ellen Connally Council Chambers",
        "address": "2079 East 9th Street, 4th Floor Cleveland, OH 44115"
    }


def test_source():
    assert parsed_items[0]["source"] == "http://council.cuyahogacounty.us/en-US/20190625ccwhl.aspx"


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "http://council.cuyahogacounty.us/ViewFile.aspx?file=100013975",
        "title": "Agenda"
    }, {
        "href": "https://www.youtube.com/embed/Ha0gyl45jHU",
        "title": "Video"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == CITY_COUNCIL


def test_all_day():
    assert parsed_items[0]["all_day"] is False
