from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_board_control import CuyaBoardControlSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_board_control.html"),
    url="http://bc.cuyahogacounty.us/en-US/Board-of-Control.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_board_control_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/090319-BOC-meeting.aspx",
)
spider = CuyaBoardControlSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 37


def test_title():
    assert parsed_item["title"] == "Board of Control"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 3, 11, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 3, 12, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_board_control/201909031100/x/board_of_control"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        **spider.location, "name": "County Headquarters 4th - Committee Room B"
    }


def test_source():
    assert parsed_item["source"] == "http://bc.cuyahogacounty.us/en-US/090319-BOC-meeting.aspx"


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=4WMJGeytOlPc09gwkgQOWA%3d%3d",
        "title": "Minutes"
    }, {
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=ItAmWexRAtkvZMENqysomw%3d%3d",
        "title": "Agenda"
    }, {
        "href": "https://www.youtube.com/embed//yMhUaaxldIg",
        "title": "Video"
    }]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
