from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_cpc import CleCpcSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_cpc.html"),
    url="https://clecpc.org/get-involved/calendar/",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cle_cpc_detail.html"),
    url="http://bc.cuyahogacounty.us/en-US/AuditCommitteeMtg-090519.aspx",
)
spider = CleCpcSpider()

freezer = freeze_time("2024-01-29")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = next(spider._parse_detail(test_detail_response), None)

freezer.stop()


def test_count():
    print(len(parsed_items))
    print(parsed_items)
    assert len(parsed_items) == 4


def test_title():
    assert parsed_item["title"] == "Police Discipline Work Group"


def test_description():
    assert (
        parsed_item["description"][0:51]
        == "Work Group to review the police disciplinary policy"
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 2, 1, 18, 30)


def test_end():
    assert parsed_item["end"] == datetime(2024, 2, 1, 20, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cle_cpc/202402011830/x/police_discipline_work_group"


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "CPC Offices",
        "address": "3631 Perkins Ave., Cleveland 4th Fl",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "http://bc.cuyahogacounty.us/en-US/AuditCommitteeMtg-090519.aspx"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "title": "Meeting agendas and minutes",
            "href": "https://clecpc.org/resources/meeting-agendas-minutes/",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
