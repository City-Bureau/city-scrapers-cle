from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cle_planning_commission import ClePlanningCommissionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cle_planning_commission.html"),
    url=ClePlanningCommissionSpider.start_urls[0],
)
spider = ClePlanningCommissionSpider()

freezer = freeze_time("2021-12-29")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 28


def test_title():
    assert parsed_items[0]["title"] == spider.title


def test_description():
    assert parsed_items[0]["description"] == spider.description


def test_start():
    assert parsed_items[0]["start"] == datetime(2021, 1, 15, 9, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "cle_planning_commission/202101150900/x/city_planning_commission"
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://planning.clevelandohio.gov/designreview/drcagenda/2021/PDF/CPC-Agenda-WebEx-meeting-011521.pdf",  # noqa
            "title": "Agenda",
        }
    ]
    # do a second test for a meeting that has a presentation as well
    assert parsed_items[2]["links"] == [
        {
            "href": "https://planning.clevelandohio.gov/designreview/drcagenda/2021/PDF/CPC-Agenda-WebEx-meeting-021921.pdf",  # noqa
            "title": "Agenda",
        },
        {
            "href": "https://planning.clevelandohio.gov/designreview/drcagenda/2021/PDF/CPC-presentation-02-19-2021.pdf",  # noqa
            "title": "Presentation",
        },
    ]


def test_classification():
    assert parsed_items[0]["classification"] == COMMISSION


def test_all_day():
    assert parsed_items[0]["all_day"] is False


def test_future_meeting_title():
    assert parsed_items[-1]["title"] == spider.title


def test_future_meeting_description():
    assert parsed_items[-1]["description"] == spider.calculated_description


def test_future_meeting_start():
    assert parsed_items[-1]["start"] == datetime(2022, 2, 4, 9, 0)


def test_future_meeting_end():
    assert parsed_items[-1]["end"] is None


def test_future_meeting_time_notes():
    assert parsed_items[-1]["time_notes"] == ""


def test_future_meeting_id():
    assert (
        parsed_items[-1]["id"]
        == "cle_planning_commission/202202040900/x/city_planning_commission"
    )


def test_future_meeting_status():
    assert parsed_items[-1]["status"] == TENTATIVE


def test_future_meeting_location():
    assert parsed_items[0]["location"] == spider.location


def test_future_meeting_source():
    assert parsed_items[-1]["source"] == test_response.url


def test_future_meeting_links():
    assert len(parsed_items[-1]["links"]) == 0


def test_future_meeting_classification():
    assert parsed_items[-1]["classification"] == COMMISSION


def test_future_meeting_all_day():
    assert parsed_items[-1]["all_day"] is False
