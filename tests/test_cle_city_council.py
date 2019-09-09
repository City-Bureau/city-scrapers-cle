import json
from datetime import datetime
from operator import itemgetter
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from freezegun import freeze_time

from city_scrapers.spiders.cle_city_council import CleCityCouncilSpider

freezer = freeze_time("2019-09-09")
freezer.start()

with open(join(dirname(__file__), "files", "cle_city_council.json"), "r", encoding="utf-8") as f:
    test_response = json.load(f)

spider = CleCityCouncilSpider()
parsed_items = sorted([item for item in spider.parse_legistar(test_response)],
                      key=itemgetter("start"))

freezer.stop()


def test_count():
    assert len(parsed_items) == 126


def test_title():
    assert parsed_items[0]["title"] == "Finance Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 7, 14, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cle_city_council/201901071400/x/finance_committee"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Mercedes Cotner Committee Room 217",
        "address": "601 Lakeside Ave Cleveland OH 44114"
    }


def test_source():
    assert parsed_items[0][
        "source"
    ] == "https://cityofcleveland.legistar.com/DepartmentDetail.aspx?ID=32369&GUID=E896EE8D-1217-4278-9410-347605F24208"  # noqa


def test_links():
    assert parsed_items[0]["links"] == [{
        "href":
            "https://cityofcleveland.legistar.com/View.ashx?M=A&ID=669085&GUID=5097DB3A-D3FD-457D-A31C-1AA4B87339EA",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


def test_all_day():
    assert parsed_items[0]["all_day"] is False
