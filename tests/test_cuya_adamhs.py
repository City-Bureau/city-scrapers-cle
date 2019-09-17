from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_adamhs import CuyaAdamhsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_adamhs.html"),
    url="http://adamhscc.org/en-US/board-minutes.aspx",
)
test_upcoming_response = file_response(
    join(dirname(__file__), "files", "cuya_adamhs_meetings.html"),
    url="http://adamhscc.org/en-US/board-meetings.aspx",
)
spider = CuyaAdamhsSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider._parse_minutes(test_response)]
parsed_upcoming_items = [item for item in spider._parse_upcoming(test_upcoming_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 24
    assert len(parsed_upcoming_items) == 8


def test_title():
    assert parsed_items[0]["title"] == "Executive Committee"
    assert parsed_upcoming_items[0]["title"] == "Finance & Operations Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2018, 9, 12, 16, 0)
    assert parsed_upcoming_items[0]["start"] == datetime(2019, 9, 18, 16, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See meeting source to confirm"


def test_id():
    assert parsed_items[0]["id"] == "cuya_adamhs/201809121600/x/executive_committee"
    assert parsed_upcoming_items[0]["id"
                                    ] == "cuya_adamhs/201909181600/x/finance_operations_committee"


def test_status():
    assert parsed_items[0]["status"] == PASSED
    assert parsed_upcoming_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == spider.location
    assert parsed_upcoming_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == "http://adamhscc.org/en-US/board-minutes.aspx"
    assert parsed_upcoming_items[0]["source"] == "http://adamhscc.org/en-US/board-meetings.aspx"


def test_links():
    assert parsed_items[0]["links"] == [{
        "href": "http://adamhscc.org/pdf_adamhscc/en-us/Minutes/Exec_091218.pdf",
        "title": "Minutes"
    }]
    assert parsed_upcoming_items[0]["links"] == [{
        "title": "Agenda",
        "href": "http://adamhscc.org/pdf_adamhscc/en-US/Finance & Operations Agenda - Sept 2019.pdf"
    }, {
        "title": "Meeting Packet",
        "href": "http://adamhscc.org/pdf_adamhscc/en-US/9.18.19 combined meeting packet.pdf"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE
    assert parsed_upcoming_items[0]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
