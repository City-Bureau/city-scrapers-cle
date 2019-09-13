from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_euclid_creek_council import CuyaEuclidCreekCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_euclid_creek_council.html"),
    url="https://www.cuyahogaswcd.org/events/2019/03/21/euclid-creek-watershed-council-meeting",
)
spider = CuyaEuclidCreekCouncilSpider()

freezer = freeze_time("2019-09-13")
freezer.start()

parsed_item = [item for item in spider._parse_meeting(test_response)][0]

freezer.stop()


def test_title():
    assert parsed_item["title"] == "Euclid Creek Watershed Council"


def test_description():
    assert parsed_item[
        "description"
    ] == """First meeting of the year of the Euclid Creek Watershed Council to approve a work plan for the year and to elect the 2019 Chair and Vice Chair of the Council.
Space limited, please RSVP."""  # noqa


def test_start():
    assert parsed_item["start"] == datetime(2019, 3, 21, 8, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 3, 21, 9, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item[
        "id"] == "cuya_euclid_creek_council/201903210800/x/euclid_creek_watershed_council"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "Mayfield Heights City Hall",
        "address": "6154 Mayfield Road Mayfield Heights, OH 44124"
    }


def test_source():
    assert parsed_item[
        "source"
    ] == "https://www.cuyahogaswcd.org/events/2019/03/21/euclid-creek-watershed-council-meeting"


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://www.cuyahogaswcd.org/files/events/ecwcchampionsprogram2019.pdf",
            "title": "ecwcchampionsprogram2019.pdf"
        },
        {
            "href": "https://www.cuyahogaswcd.org/files/events/ecwcagendamar212019.pdf",
            "title": "Agenda"
        },
        {
            "href": "https://www.cuyahogaswcd.org/files/events/ecwcdraftminutesjuly262018.pdf",
            "title": "Minutes"
        },
        {
            "href": "https://www.cuyahogaswcd.org/files/events/pipe2019workplanfebruaryupdate.pdf",
            "title": "pipe2019workplanfebruaryupdate.pdf"
        },
        {
            "href": "https://www.cuyahogaswcd.org/files/events/ecwc2019draftworkplan.pdf",
            "title": "ecwc2019draftworkplan.pdf"
        },
        {
            "href":
                "https://www.cuyahogaswcd.org/files/events/2018-euclidcreekwatershedpechakuchaecwc.pdf",  # noqa
            "title": "2018-euclidcreekwatershedpechakuchaecwc.pdf"
        },
        {
            "href":
                "https://www.cuyahogaswcd.org/files/events/euclidcreeknps-is1.2draftforinput03132019.pdf",  # noqa
            "title": "euclidcreeknps-is1.2draftforinput03132019.pdf"
        }
    ]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
