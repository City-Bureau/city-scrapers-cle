from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_personnel_review_commission import (
    CuyaPersonnelReviewCommissionSpider,
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_personnel_review_commission.html"),
    url="https://cuyahogacounty.gov/personnel-review-commission/calendar",
)
spider = CuyaPersonnelReviewCommissionSpider()

freezer = freeze_time(datetime(2024, 8, 14, 13, 1))
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = parsed_items[0]
freezer.stop()


def test_title():
    assert parsed_item["title"] == "Personnel Review Commission Meeting - 08/07/23 "


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 8, 7, 16, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 8, 7, 17, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_personnel_review_commission/202408071600/x/personnel_review_commission_meeting_08_07_23"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "9830 Lorain Ave., Classroom 5 Cleveland, Ohio 44102",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/personnel-review-commission/calendar"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/agendas/080724-prcagenda.pdf?sfvrsn=b2d2fb6c_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
