from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_transit import CleTransitSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_transit.html"),
    url="http://www.riderta.com/events/2019/8/6/committee-meetings",
)
spider = CleTransitSpider()

freezer = freeze_time("2019-09-12")
freezer.start()

parsed_item = [item for item in spider._parse_meeting(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Standing Committees"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 8, 6, 9, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cle_transit/201908060900/x/standing_committees"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "RTA Main Office",
        "address": "1240 West 6th St Board Room Cleveland, OH 44113"
    }


def test_source():
    assert parsed_item["source"] == "http://www.riderta.com/events/2019/8/6/committee-meetings"


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06CmtAgendas.pdf",
            "title": "2019-08-06CmtAgendas.pdf"
        },
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06FarePolicy.pdf",
            "title": "2019-08-06FarePolicy.pdf"
        },
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06CNGTriskett_0.pdf",
            "title": "2019-08-06CNGTriskett.pdf"
        },
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06VanPool.pdf",
            "title": "2019-08-06VanPool.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06DCADiscountFareProgram.pdf",  # noqa
            "title": "2019-08-06DCADiscountFareProgram.pdf"
        },
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06MedinaCounty.pdf",
            "title": "2019-08-06MedinaCounty.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06CasualtyInsProgram.pdf",  # noqa
            "title": "2019-08-06CasualtyInsProgram.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06IA2ndQuarter2019.pdf",
            "title": "2019-08-06IA2ndQuarter2019.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06ExternalStakholderMinutes.pdf",  # noqa
            "title": "2019-08-06ExternalStakholderMinutes.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06OrganizationalMinutes.pdf",  # noqa
            "title": "2019-08-06OrganizationalMinutes.pdf"
        },
        {
            "href":
                "http://www.riderta.com/sites/default/files/events/2019-08-06OperationalMinutes.pdf",  # noqa
            "title": "2019-08-06OperationalMinutes.pdf"
        },
        {
            "href": "http://www.riderta.com/sites/default/files/events/2019-08-06AuditMinutes.pdf",
            "title": "2019-08-06AuditMinutes.pdf"
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
