from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_homeless_services import CuyaHomelessServicesSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_homeless_services.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/cleveland-cuyahoga-office-of-homeless-services-advisory-board",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_homeless_services_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/16/boards-and-commissions/11-16-23-ohs-advisory-board",  # noqa
)
spider = CuyaHomelessServicesSpider()

freezer = freeze_time("2024-1-14")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "11/16/23 OHS Advisory Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 11, 16, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 11, 16, 11, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_homeless_services/202311160900/x/11_16_23_ohs_advisory_board"  # noqa
    )


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Office of Health and Human Services",
        "address": "310 West Lakeside Avenue, 5th Floor, Cleveland, Ohio 44113",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/11/16/boards-and-commissions/11-16-23-ohs-advisory-board"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/11162023-ohsadvbrdagenda.pdf?sfvrsn=bdac935a_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
