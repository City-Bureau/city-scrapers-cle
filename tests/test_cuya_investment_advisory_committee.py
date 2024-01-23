from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_investment_advisory_committee import (
    CuyaInvestmentAdvisoryCommitteeSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_investment_advisory_committee.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/investment-advisory-committee",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_investment_advisory_committee_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/25/boards-and-commissions/investment-advisory-committee-meeting---1-25-24",  # noqa
)
spider = CuyaInvestmentAdvisoryCommitteeSpider()

freezer = freeze_time("2024-01-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Investment Advisory Committee Meeting - 1/25/24"


def test_description():
    assert (
        parsed_item["description"] == "Stream: https://www.youtube.com/cuyahogacounty"
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 25, 10, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 1, 25, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_investment_advisory_committee/202401251000/x/investment_advisory_committee_meeting_1_25_24" # noqa
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "Cuyahoga County Headquarters 4-407",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/25/boards-and-commissions/investment-advisory-committee-meeting---1-25-24" # noqa
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
