from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_tax_incentive_review import CuyaTaxIncentiveReviewSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_tax_incentive_review.html"),
    url="http://bc.cuyahogacounty.us/en-US/Tax-Incentive-Review-Council.aspx",
)
spider = CuyaTaxIncentiveReviewSpider()

freezer = freeze_time("2019-09-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 31


def test_title():
    assert parsed_items[0]["title"] == "Tax Incentive Review Council - Broadview Hts."


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 7, 16, 13, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cuya_tax_incentive_review/201907161300/x/tax_incentive_review_council_broadview_hts_"  # noqa
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == []


def test_classification():
    assert parsed_items[0]["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
