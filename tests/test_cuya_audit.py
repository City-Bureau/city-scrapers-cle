from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_audit import CuyaAuditSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_audit.html"),
    url="http://bc.cuyahogacounty.us/en-US/Audit-Committee.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_audit_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/AuditCommitteeMtg-090519.aspx",
)
spider = CuyaAuditSpider()

freezer = freeze_time("2019-09-19")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "Audit Committee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 5, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 5, 23, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_audit/201909050900/x/audit_committee"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"
                       ] == "http://bc.cuyahogacounty.us/en-US/AuditCommitteeMtg-090519.aspx"


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=9RBPLk%2fewj3DObNVTeTkjQ%3d%3d",
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
