from datetime import datetime
from operator import itemgetter
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_planning_commission import ClePlanningCommissionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_planning_commission.html"),
    url="http://planning.city.cleveland.oh.us/designreview/schedule.php",
)
test_agenda_response = file_response(
    join(dirname(__file__), "files", "cle_planning_commission_agenda.html"),
    url="http://planning.city.cleveland.oh.us/designreview/drcagenda/2019/06072019/index.php",
)
spider = ClePlanningCommissionSpider()

freezer = freeze_time("2019-09-09")
freezer.start()

parsed_agenda = [p for p in spider._parse_agenda(test_agenda_response)][0]
parsed_items = sorted(
    [item for item in spider._parse_table_rows(test_response, [datetime(2019, 6, 7).date()])],
    key=itemgetter("start"),
)

freezer.stop()


def test_count():
    assert len(parsed_items) == 23


def test_title():
    assert parsed_items[0]["title"] == "City Planning Commission"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 4, 9, 0)
    assert parsed_agenda["start"] == datetime(2019, 6, 7, 9)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"
                           ] == "cle_planning_commission/201901040900/x/city_planning_commission"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"
                           ] == "http://planning.city.cleveland.oh.us/designreview/schedule.php"
    assert parsed_agenda[
        "source"
    ] == "http://planning.city.cleveland.oh.us/designreview/drcagenda/2019/06072019/index.php"


def test_links():
    assert parsed_items[0]["links"] == []
    assert parsed_agenda["links"] == [{
        "href":
            "http://planning.city.cleveland.oh.us/designreview/drcagenda/2019/06072019/CPC-DRAFT-Agenda060719.pdf",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False
