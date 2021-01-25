from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_citizens_advisory_equity import (
    CuyaCitizensAdvisoryEquitySpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_citizens_advisory_equity.html"),
    url="http://bc.cuyahogacounty.us/en-US/Citizens-Advisory-Council-Equity.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_citizens_advisory_equity_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/12172020-citizens-advisory.aspx",
)
spider = CuyaCitizensAdvisoryEquitySpider()

freezer = freeze_time("2021-01-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Citizens’ Advisory Council on Equity"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2020, 12, 17, 15, 0)


def test_end():
    assert parsed_item["end"] == datetime(2020, 12, 17, 16, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_citizens_advisory_equity/202012171500/x/citizens_advisory_council_on_equity"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Remote",
        "address": "",
    }


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=6M9ljYUOx9F9%2fb6%2fYdjOWQ%3d%3d",  # noqa
            "title": "Agenda",
        },
        {"href": "https://www.youtube.com/embed//3GZE1T68czc", "title": "Video"},
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
