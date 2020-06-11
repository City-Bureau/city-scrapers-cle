from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import CANCELLED, COMMISSION
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_personnel_review_commission import (
    CuyaPersonnelReviewCommissionSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_personnel_review_commission.html"),
    url="https://prc.cuyahogacounty.us/en-US/PRC-Meetings-Resolutions.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_personnel_review_commission_detail.html"),
    url="https://prc.cuyahogacounty.us/en-US/071019-PRC-Mtg.aspx",
)
spider = CuyaPersonnelReviewCommissionSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 12


def test_title():
    assert parsed_item["title"] == "Personnel Review Commission"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 7, 10, 16, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 7, 10, 17, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_personnel_review_commission/201907101600/x/personnel_review_commission"
    )


def test_status():
    assert parsed_item["status"] == CANCELLED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2429 Superior Viaduct, Third Floor, Cleveland, OH 44113",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://prc.cuyahogacounty.us/en-US/071019-PRC-Mtg.aspx"
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
