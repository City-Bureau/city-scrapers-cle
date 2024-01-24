from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_technical_advisory_committee import (
    CuyaTechnicalAdvisoryCommitteeSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_technical_advisory_committee.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/technical-advisory-committee",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_technical_advisory_committee_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/09/boards-and-commissions/technical-advisory-committee-meeting---11-09-23",  # noqa
)
spider = CuyaTechnicalAdvisoryCommitteeSpider()

freezer = freeze_time("2024-01-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 25


def test_title():
    assert parsed_item["title"] == "Technical Advisory Committee Meeting - 11/09/23"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 11, 9, 9, 30)


def test_end():
    assert parsed_item["end"] == datetime(2023, 11, 9, 10, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_technical_advisory_committee/202311090930/x/technical_advisory_committee_meeting_11_09_23"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "Microsoft Teams Remote",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/09/boards-and-commissions/technical-advisory-committee-meeting---11-09-23"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/tac/2023/110923-tacagenda.pdf?sfvrsn=53d7d767_1",  # noqa
            "title": "Agenda",
        },
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/tac/2023/110923-tacminutes.pdf?sfvrsn=2612a446_1",  # noqa
            "title": "Minutes",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
