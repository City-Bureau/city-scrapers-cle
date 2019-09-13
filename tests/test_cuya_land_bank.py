from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_land_bank import CuyaLandBankSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_land_bank.html"),
    url="http://www.cuyahogalandbank.org/board_meetings/20180928/",
)
spider = CuyaLandBankSpider()

freezer = freeze_time("2019-09-13")
freezer.start()

parsed_item = [item for item in spider._parse_meeting(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Board of Directors"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2018, 9, 28, 10, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == "See agenda and notice to confirm details"


def test_id():
    assert parsed_item["id"] == "cuya_land_bank/201809281000/x/board_of_directors"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == "http://www.cuyahogalandbank.org/board_meetings/20180928/"


def test_links():
    assert parsed_item["links"] == [
        {
            "href":
                "http://www.cuyahogalandbank.org/board_meetings/20180928/20180928_Notice_of_Meeting.pdf",  # noqa
            "title": "Notice"
        },
        {
            "href":
                "http://www.cuyahogalandbank.org/board_meetings/20180928/20180928_agenda_cclrc_board.pdf",  # noqa
            "title": "Agenda"
        },
        {
            "href":
                "http://www.cuyahogalandbank.org/board_meetings/20180928/20180928_Minutes_of_Meeting.pdf",  # noqa
            "title": "Minutes"
        },
        {
            "href": "http://www.cuyahogalandbank.org/board_meetings/20180928/20180928_1_adopted.pdf",  # noqa
            "title": "Resolution 1"
        },
        {
            "href": "http://www.cuyahogalandbank.org/board_meetings/20180928/20180928_2_adopted.pdf",  # noqa
            "title": "Resolution 2"
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
