from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_design_review import CleDesignReviewSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_design_review.html"),
    url=(
        "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    ),
)
spider = CleDesignReviewSpider()

freezer = freeze_time("2021-12-01")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 118


def test_title():
    assert parsed_items[0]["title"] == "Downtown/Flats Design Review Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2021, 1, 14, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "Due to Covid meetings are generally being held on WebEx rather than in person. For more information contact asantora@clevelandohio.gov"


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cle_design_review/202101140900/x/downtown_flats_design_review_committee"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }
 

def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    )


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://planning.clevelandohio.gov/designreview/drcagenda/2021/PDF/CPC-Agenda-WebEx-meeting-011421.pdf",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False

# There's a second set of tests to make sure that we're correclty parsing out details for meetings based on calculated times

def test_future_meeting_title():
    assert parsed_items[-1]["title"] == "Southeast  Design Review Committee"


def test_future_meeting_description():
    assert parsed_items[-1]["description"] == ""


def test_future_meeting_start():
    assert parsed_items[-1]["start"] == datetime(2021, 12, 22, 17, 0)


def test_future_meeting_end():
    assert parsed_items[-1]["end"] is None


def test_future_meeting_time_notes():
    assert parsed_items[-1]["time_notes"] == "Due to Covid meetings are generally being held on WebEx rather than in person. For more information contact mfields@clevelandohio.gov"


def test_future_meeting_id():
    assert (
        parsed_items[-1]["id"]
        == "cle_design_review/202112221700/x/southeast_design_review_committee"
    )


def test_future_meeting_status():
    assert parsed_items[-1]["status"] == TENTATIVE


def test_future_meeting_location():
    assert parsed_items[-1]["location"] == {
        "name": "York-Rite Mason Temple",
        "address": "13512 Kinsman Road Cleveland, OH",
    }

def test_future_meeting_source():
    assert (
        parsed_items[-1]["source"]
        == "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    )


def test_future_meeting_links():
    assert len(parsed_items[-1]["links"]) == 0


def test_future_meeting_classification():
    assert parsed_items[-1]["classification"] == ADVISORY_COMMITTEE


def test_future_meeting_all_day():
    assert parsed_items[-1]["all_day"] is False
