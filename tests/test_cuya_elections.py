from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_elections import CuyaElectionsSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_elections.html"),
    url="https://boe.cuyahogacounty.gov/calendar/event-details/2022/05/24/default-calendar/board-meeting",
)
spider = CuyaElectionsSpider()

freezer = freeze_time("2022-04-28")
freezer.start()

parsed_items = [item for item in spider._parse_detail(test_response)]

freezer.stop()


# def test_tests():
#     print("Please write some tests for this spider or at least disable this one.")
#     assert False


"""
Uncomment below
"""

def test_title():
    print(parsed_items[0]["title"])
    assert parsed_items[0]["title"] == "Board Meeting"


def test_description():
    assert parsed_items[0]["description"] == "Certification of the May 3, 2022 Primary Election"


def test_start():
    assert parsed_items[0]["start"] == datetime(2022, 5, 24, 9, 30)


def test_end():
    assert parsed_items[0]["end"] == datetime(2022, 5, 24, 10, 30)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


# def test_id():
#     assert parsed_items[0]["id"] == "EXPECTED ID"


# def test_status():
#     assert parsed_items[0]["status"] == "EXPECTED STATUS"


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "",
        "address": "2925 Euclid Ave\nCleveland"
    }


def test_source():
    assert parsed_items[0]["source"] == "https://boe.cuyahogacounty.gov/calendar/event-details/2022/05/24/default-calendar/board-meeting"


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://boe.cuyahogacounty.gov/about-us/board-meeting-documents",
            "title": "See Board Meeting Documents on our About Us page"
        },
        {
            "href": "https://boe.cuyahogacounty.gov/Sitefinity/Public/Services/ICalanderService/file.ics/?id=c6380639-23da-4c05-b387-d7e9f13f8928&provider=&uiculture=en",
            "title": "Outlook"
        },
        {
            "href": "https://boe.cuyahogacounty.gov/Sitefinity/Public/Services/ICalanderService/file.ics/?id=c6380639-23da-4c05-b387-d7e9f13f8928&provider=&uiculture=en",
            "title": "ICal"
        },
        {
            "href": "http://www.google.com/calendar/event?action=TEMPLATE&text=Board+Meeting&dates=20220524T133000Z/20220524T143000Z&location=Ohio%2cCleveland%2c2925+Euclid+Ave&sprop=website:https://boe.cuyahogacounty.gov&sprop=name:Board+Meeting&details=Certification+of+the+May+3%2c+2022+Primary+Election%0a%0aSee+Board+Meeting+Documents+on+our+About+Us+page&recur=",
            "title": "Google Calendar"
        }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


# @pytest.mark.parametrize("item", parsed_items)
# def test_all_day(item):
#     assert item["all_day"] is False
