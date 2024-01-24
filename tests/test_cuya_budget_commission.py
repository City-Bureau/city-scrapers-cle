from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_budget_commission import CuyaBudgetCommissionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_budget_commission.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/budget-commission",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_budget_commission_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/02/05/boards-and-commissions/budget-commission-meeting---02-05-23",  # noqa
)
spider = CuyaBudgetCommissionSpider()

freezer = freeze_time("2024-01-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Budget Commission Meeting - 02/05/24"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 2, 5, 10, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 2, 5, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_budget_commission/202402051000/x/budget_commission_meeting_02_05_24"
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 East Ninth Street, Fiscal Rm 3-114, Cleveland, OH 44115",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/02/05/boards-and-commissions/budget-commission-meeting---02-05-23"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/bc/2023/020524-bcagenda.pdf?sfvrsn=3802e8ba_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
