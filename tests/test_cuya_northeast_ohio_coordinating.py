from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_northeast_ohio_coordinating import (
    CuyaNortheastOhioCoordinatingSpider
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_northeast_ohio_coordinating.html"),
    url=(
        "https://www.noaca.org/board-committees/noaca-board-and-committees/agendas-and-presentations/-toggle-all"  # noqa
    )
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_northeast_ohio_coordinating_detail.html"),
    url="https://www.noaca.org/Home/Components/Calendar/Event/8261/7639?toggle=all&npage=2"
)
spider = CuyaNortheastOhioCoordinatingSpider()

freezer = freeze_time("2019-10-04")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 20


def test_title():
    assert parsed_item["title"] == "Transportation Subcommittee"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 9, 20, 14, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 9, 20, 16, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item[
        "id"] == "cuya_northeast_ohio_coordinating/201909201430/x/transportation_subcommittee"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "NOACA",
        "address": "1299 Superior Avenue Cleveland, OH 44114-3204",
    }


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [{
        "href": "https://www.noaca.org/home/showdocument?id=24219",
        "title":
            "Project Planning Review (PPR)/Intergovernmental Review and "
            "Consultation (IGRC): 2nd Quarter State Fiscal Year (SFY) 2020"
    }, {
        "href": "https://www.noaca.org/home/showdocument?id=24217",
        "title": "Plan and TIP Amendment: 2nd Quarter SFY 2020"
    }, {
        "href": "https://www.noaca.org/home/showdocument?id=24221",
        "title": "Functional Classification Amendment Recommendations"
    }, {
        "href": "https://www.noaca.org/home/showdocument?id=24225",
        "title": "Safety Performance Target Setting for Calendar Year 2020"
    }, {
        "href": "https://www.noaca.org/home/showdocument?id=24227",
        "title":
            "Enhanced Mobility for Seniors and Individuals with Disabilities "
            "(Section 5310) Program Update"
    }, {
        "href": "https://www.noaca.org/home/showdocument?id=24223",
        "title": "NOACA Project Maintenance Monitoring Program"
    }, {
        "href": "https://www.noaca.org/Home/ShowDocument?id=24167",
        "title": "Transportation Subcommittee Packet Sept. 2019"
    }]


def test_classification():
    assert parsed_item["classification"] == COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
