from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_landmarks import CleLandmarksSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_landmarks.html"),
    url="http://planning.city.cleveland.oh.us/landmark/AGENDALIST.html",
)
test_agenda_response = file_response(
    join(dirname(__file__), "files", "cle_landmarks_agenda.html"),
    url="http://planning.city.cleveland.oh.us/landmark/agenda/2019/09122019/index.php",
)
spider = CleLandmarksSpider()

freezer = freeze_time("2019-09-11")
freezer.start()

parsed_dates = sorted([item for item in spider._parse_table_starts(test_response, "2019")])
parsed_agenda = [item for item in spider._parse_agenda(test_agenda_response)][0]
freezer.stop()


def test_count():
    assert len(parsed_dates) == 23


def test_title():
    assert parsed_agenda["title"] == "Landmarks Commission"


def test_description():
    assert parsed_agenda["description"] == ""


def test_start():
    assert parsed_agenda["start"] == datetime(2019, 9, 12, 9, 0)


def test_end():
    assert parsed_agenda["end"] is None


def test_time_notes():
    assert parsed_agenda["time_notes"] == ""


def test_id():
    assert parsed_agenda["id"] == "cle_landmarks/201909120900/x/landmarks_commission"


def test_status():
    assert parsed_agenda["status"] == TENTATIVE


def test_location():
    assert parsed_agenda["location"] == spider.location


def test_source():
    assert parsed_agenda[
        "source"] == "http://planning.city.cleveland.oh.us/landmark/agenda/2019/09122019/index.php"


def test_links():
    assert parsed_agenda["links"] == [{
        "href":
            "http://planning.city.cleveland.oh.us/landmark/agenda/2019/08222019/CLC-8-22-19-AGENDA.pdf",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_agenda["classification"] == COMMISSION


def test_all_day():
    assert parsed_agenda["all_day"] is False
