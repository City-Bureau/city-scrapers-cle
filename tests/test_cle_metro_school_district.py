from datetime import datetime
from operator import itemgetter
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.http import XmlResponse

from city_scrapers.spiders.cle_metro_school_district import CleMetroSchoolDistrictSpider

init_test_response = file_response(
    join(dirname(__file__), "files", "cle_metro_school_district.xml"),
    url="https://www.boarddocs.com/oh/cmsd/board.nsf/XML-ActiveMeetings",
)
test_response = XmlResponse(
    url=init_test_response.url, request=init_test_response.request, body=init_test_response.body
)
spider = CleMetroSchoolDistrictSpider()

freezer = freeze_time("2019-09-09")
freezer.start()

parsed_items = sorted([item for item in spider.parse(test_response)], key=itemgetter("start"))

freezer.stop()


def test_count():
    assert len(parsed_items) == 250


def test_title():
    assert parsed_items[0]["title"] == "2009 Organization Meeting/Work Session"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2009, 1, 13, 18, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0][
        "id"] == "cle_metro_school_district/200901131830/x/2009_organization_meeting_work_session"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Board of Education Administration Building Board Room",
        "address": "1111 Superior Ave E, Cleveland, OH 44114"
    }
    assert parsed_items[-1]["location"] == {
        "address": "1111 Superior Avenue, 4th Floor Conference Room, Cleveland, OH 44114",
        "name": "Cleveland Municipal School District Administrative Offices",
    }


def test_source():
    assert parsed_items[-1][
        "source"] == "http://go.boarddocs.com/oh/cmsd/Board.nsf/goto?open&id=B7CTJX75F93D"


def test_links():
    assert parsed_items[-1]["links"] == [{
        "href": "http://go.boarddocs.com/oh/cmsd/Board.nsf/goto?open&id=B7CTJX75F93D",
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
