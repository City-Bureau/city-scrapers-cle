from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_metrohealth import CuyaMetrohealthSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_metrohealth.html"),
    url="https://www.metrohealth.org/about-us/board-and-governance/meetings",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_metrohealth_detail.html"),
    url="https://www.metrohealth.org/about-us/board-and-governance/meetings/09-2018",
)
spider = CuyaMetrohealthSpider()

freezer = freeze_time("2019-09-25")
freezer.start()

parsed_main_items = [item for item in spider.parse(test_response)]
parsed_items = [item for item in spider._parse_detail(test_detail_response)]

freezer.stop()


def test_count():
    assert len(parsed_main_items) == 24
    assert len(parsed_items) == 4


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2018, 9, 26, 8, 0)


def test_end():
    assert parsed_items[0]["end"] == datetime(2018, 9, 26, 10, 0)


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See source to confirm details"


def test_id():
    assert parsed_items[0]["id"] == "cuya_metrohealth/201809260800/x/board_of_trustees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == test_detail_response.url


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href":
                "https://www.metrohealth.org/-/media/metrohealth/documents/about-us/board/meetings/2018/09_september/sept2018-bot-agenda.pdf?la=en&hash=E039383B98366D9ABB4AF4D820E30009D8DED50A",  # noqa
            "title": "Agenda"
        },
        {
            "href":
                "https://www.metrohealth.org/-/media/metrohealth/documents/about-us/board/meetings/2018/09_september/sept2018-bot-minutes.pdf?la=en&hash=6E58528D3F4AAFE3F888A429AE7F61D1DC0C91A8",  # noqa
            "title": "Minutes"
        },
        {
            "href":
                "https://www.metrohealth.org/-/media/metrohealth/documents/about-us/board/meetings/2018/09_september/sept2018-bot-presidentsreport.pdf?la=en&hash=5293380F4E11A5E5CD94FA1EFF1E0B63EBBEE39C",  # noqa
            "title": "President's Report"
        },
        {
            "href":
                "https://www.metrohealth.org/-/media/metrohealth/documents/about-us/board/meetings/2018/09_september/sept2018-bot-resolutions---public.pdf?la=en&hash=8FD98573CF0EA2F3A5ACFB143B0312A0938446E8",  # noqa
            "title": "Resolutions"
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
