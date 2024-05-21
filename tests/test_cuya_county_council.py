from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_county_council import CuyaCountyCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_county_council.json"),
    url="https://www.cuyahogacounty.gov/web-interface/events?StartDate=2024-02-17T11:13:35&EndDate=2024-08-15T11:13:35&EventSchedulerViewMode=month&UICulture=&Id=175b0fba-07f2-4b3e-a794-e499e98c0a93&CurrentPageId=b38b8f62-8073-4d89-9027-e7a13e53248e&sf_site=f3ea71cd-b8c9-4a53-b0db-ee5d552472fc",  # noqa
)
spider = CuyaCountyCouncilSpider()

freezer = freeze_time("2024-04-18")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = parsed_items[0]
freezer.stop()


def test_title():
    assert (
        parsed_item["title"]
        == "Public Works, Procurement & Contracting Committee Meeting - 02/21/2024"  # noqa
    )


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2024, 2, 21, 10, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_county_council/202402211000/x/public_works_procurement_contracting_committee_meeting_02_21_2024"  # noqa
    )


def test_status():
    assert parsed_item["status"] == "passed"


def test_location():
    assert parsed_item["location"] == {
        "address": "4th Floor 2079 East 9th Street",
        "name": "C. Ellen Connally Council Chambers",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.cuyahogacounty.gov/web-interface/events?StartDate=2024-02-17T11:13:35&EndDate=2024-08-15T11:13:35&EventSchedulerViewMode=month&UICulture=&Id=175b0fba-07f2-4b3e-a794-e499e98c0a93&CurrentPageId=b38b8f62-8073-4d89-9027-e7a13e53248e&sf_site=f3ea71cd-b8c9-4a53-b0db-ee5d552472fc"  # noqa
    )


def test_links():
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == COMMISSION


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
