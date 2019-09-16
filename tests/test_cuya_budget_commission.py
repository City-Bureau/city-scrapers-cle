from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_budget_commission import CuyaBudgetCommissionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_budget_commission.html"),
    url="http://bc.cuyahogacounty.us/en-US/Budget-Commission.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_budget_commission_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/080519-BC-meeting.aspx",
)
spider = CuyaBudgetCommissionSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 2


def test_title():
    assert parsed_item["title"] == "Budget Commission"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 8, 5, 10, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 8, 5, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_budget_commission/201908051000/x/budget_commission"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Cuyahoga County Headquarters",
        "address": "2079 East Ninth Street, Fiscal Rm 3-114, Cleveland, OH 44115",
    }


def test_source():
    assert parsed_item["source"] == "http://bc.cuyahogacounty.us/en-US/080519-BC-meeting.aspx"


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://bc.cuyahogacounty.us/ViewFile.aspx?file=8jA%2fdFNXxbMOPJEUFXlVnw%3d%3d",
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
