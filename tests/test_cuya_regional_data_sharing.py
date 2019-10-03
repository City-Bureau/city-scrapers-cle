from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_regional_data_sharing import CuyaRegionalDataSharingSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_regional_data_sharing.html"),
    url="http://bc.cuyahogacounty.us/en-US/CRIS.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_regional_data_sharing_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/040519-REDSS-meeting.aspx",
)
spider = CuyaRegionalDataSharingSpider()

freezer = freeze_time("2019-10-03")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 3


def test_title():
    assert parsed_item["title"] == "Governing Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 4, 5, 14, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 4, 5, 15, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_regional_data_sharing/201904051400/x/governing_board"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=yC5L9gSioQrD%2bnXtN%2bErfg%3d%3d",
        "title": "Minutes"
    }, {
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=yC5L9gSioQr6HqvCS4du4g%3d%3d",
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
