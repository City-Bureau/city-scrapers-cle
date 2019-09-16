from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_public_defenders_commission import (
    CuyaPublicDefendersCommissionSpider
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_public_defenders_commission.html"),
    url="http://publicdefender.cuyahogacounty.us/en-US/Event_calendar.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_public_defenders_commission_detail.html"),
    url="http://publicdefender.cuyahogacounty.us/en-US/09042019CommissionMeeting.aspx",
)
spider = CuyaPublicDefendersCommissionSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Public Defenders Commission"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 4, 16, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item[
        "id"] == "cuya_public_defenders_commission/201909041630/x/public_defenders_commission"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item[
        "source"] == "http://publicdefender.cuyahogacounty.us/en-US/09042019CommissionMeeting.aspx"


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
