from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_health import CuyaHealthSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_health.html"),
    url="https://ccbh.net/board-minutes-agenda/",
)

spider = CuyaHealthSpider()

freezer = freeze_time("2024-02-07")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
# Assuming this is the correct item you're testing; adjust as necessary
parsed_item = parsed_items[0]
freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "Board meeting (Dec 20, 2023)"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 12, 20, 0, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""  # Adjust if there's a specific note


def test_id():
    assert parsed_item["id"] == "cuya_health/202312200000/x/board_meeting_dec_20_2023_"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    expected_location = {
        "name": "Cuyahoga County Board of Health",
        "address": "5550 Venture Dr, Parma, OH 44130",
    }
    assert parsed_item["location"] == expected_location


def test_source():
    assert parsed_item["source"] == "https://ccbh.net/board-minutes-agenda/"


def test_links():
    expected_links = [
        {
            "href": "https://ccbh.net/wp-content/uploads/2024/01/01.00-December_2023_Board_Agenda-Revised_12-19-2023.pdf",  # noqa
            "title": "Agenda",
        },
        {
            "href": "https://ccbh.net/wp-content/uploads/2024/01/December_20_2023-Minutes-1.pdf",  # noqa
            "title": "Minutes",
        },
    ]
    assert parsed_item["links"] == expected_links


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
