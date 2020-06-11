from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_community_college import CuyaCommunityCollegeSpider

test_agenda_response = file_response(
    join(dirname(__file__), "files", "cuya_community_college_agenda.pdf"),
    url="https://www.tri-c.edu/administrative-departments/documents/board-meeting-agenda.pdf",  # noqa
    mode="rb",
)
test_response = file_response(
    join(dirname(__file__), "files", "cuya_community_college.pdf"),
    url="https://www.tri-c.edu/administrative-departments/documents/board-meetings-calendar.pdf",  # noqa
    mode="rb",
)
spider = CuyaCommunityCollegeSpider()

freezer = freeze_time("2019-10-07")
freezer.start()

spider.agenda_map = {}
spider._parse_agenda(test_agenda_response)
parsed_items = [item for item in spider._parse_calendar(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 7


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 9, 26, 13, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cuya_community_college/201909261330/x/board_of_trustees"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Jerry Sue Thornton Center - Ford Room",
        "address": "2500 E 22nd St, Cleveland, OH 44115",
    }


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {"href": test_agenda_response.url, "title": "Agenda"}
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
