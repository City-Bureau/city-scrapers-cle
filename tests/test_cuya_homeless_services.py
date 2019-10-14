from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_homeless_services import CuyaHomelessServicesSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_homeless_services.html"),
    url="http://ohs.cuyahogacounty.us/en-US/Advisory-Board.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_homeless_services_detail.html"),
    url="http://ohs.cuyahogacounty.us/en-US/091219-Advisory-meeting.aspx",
)
spider = CuyaHomelessServicesSpider()

freezer = freeze_time("2019-10-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_item["title"] == "Advisory Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 12, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 12, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_homeless_services/201909120900/x/advisory_board"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://ohs.cuyahogacounty.us/ViewFile.aspx?file=HrgG0wNlU4uuMnY1ORPT2g%3d%3d",
        "title": "Minutes"
    }, {
        "href": "http://ohs.cuyahogacounty.us/ViewFile.aspx?file=HrgG0wNlU4sH90cSRjQZyw%3d%3d",
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
