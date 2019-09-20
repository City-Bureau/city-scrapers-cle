from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_arts_culture import CuyaArtsCultureSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture.html"),
    url="https://www.cacgrants.org/about-us/board/board-meeting-schedule/",
)
test_minutes_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_minutes.html"),
    url="https://www.cacgrants.org/about-us/board/board-materials/",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_detail.html"),
    url="https://www.cacgrants.org/about-us/board/board-meeting-2019-04-10/",
)
spider = CuyaArtsCultureSpider()

freezer = freeze_time("2019-09-19")
freezer.start()

spider._parse_minutes(test_minutes_response)
parsed_items = [item for item in spider._parse_schedule(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "Board of Trustees Annual Meeting"


def test_description():
    assert parsed_item["description"] == """All are invited to join Cuyahoga Arts & Culture at its Board of Trustees' annual meeting on Wednesday, April 24, 2019 at 3:30 pm at The Dealership, 3558 Lee Road, Shaker Heights, OH 44120.

At the meeting, the Board of Trustees will discuss and take action on grantmaking guidelines for the 2020-21 General Operating Support and 2020 Project Support grant programs; take action on administrative matters, including the annual election of officers and reappointment of members to the Audit & Finance Advisory Committee; and, provide an update on the search for CAC’s next Executive Director.

CAC's Board meetings are always open to the public."""  # noqa


def test_start():
    assert parsed_item["start"] == datetime(2019, 4, 24, 15, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_arts_culture/201904241530/x/board_of_trustees_annual_meeting"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "The Dealership",
        "address": "3558 Lee Road, Shaker Heights, OH 44120"
    }


def test_source():
    assert parsed_item["source"
                       ] == "https://www.cacgrants.org/about-us/board/board-meeting-2019-04-10/"


def test_links():
    assert parsed_item["links"] == [
        {
            "href":
                "https://www.cacgrants.org/assets/ce/Documents/2019/2019-04-24-CAC-Board-Meeting-Handouts.pdf",  # noqa
            "title": "Agenda and Handouts"
        },
        {
            "href":
                "https://www.cacgrants.org/assets/ce/Documents/2019/2019-04-24-Annual-Meeting-Minutes.pdf",  # noqa
            "title": "Minutes"
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
