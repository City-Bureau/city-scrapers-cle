from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, CANCELLED, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_port_authority import CuyaPortAuthoritySpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_port_authority.html"),
    url="http://www.portofcleveland.com/about-the-port/board-meeting-information/",
)
spider = CuyaPortAuthoritySpider()

freezer = freeze_time("2019-10-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 23


def test_title():
    assert parsed_items[5]["title"] == "Board of Directors Special Meeting"


def test_description():
    assert parsed_items[5]["description"] == ""


def test_start():
    assert parsed_items[5]["start"] == datetime(2019, 5, 22, 8, 30)


def test_end():
    assert parsed_items[5]["end"] is None


def test_time_notes():
    assert parsed_items[5]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[5]["id"]
        == "cuya_port_authority/201905220830/x/board_of_directors_special_meeting"
    )


def test_status():
    assert parsed_items[0]["status"] == CANCELLED
    assert parsed_items[5]["status"] == PASSED


def test_location():
    assert parsed_items[5]["location"] == spider.location


def test_source():
    assert parsed_items[5]["source"] == test_response.url


def test_links():
    assert parsed_items[5]["links"] == [
        {
            "href": "http://www.portofcleveland.com/media/1346/minutes-05222019.pdf",
            "title": "Minutes",
        }
    ]


def test_classification():
    assert parsed_items[5]["classification"] == BOARD


def test_all_day():
    assert parsed_items[5]["all_day"] is False
