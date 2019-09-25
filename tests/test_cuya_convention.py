from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_convention import CuyaConventionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_convention.html"),
    url="http://www.cccfdc.org/",
)
spider = CuyaConventionSpider()

freezer = freeze_time("2019-09-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 17


def test_title():
    assert parsed_items[0]["title"] == "Board of Directors"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 1, 25, 8, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert parsed_items[0]["id"] == "cuya_convention/201901250800/x/board_of_directors"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0]["source"] == "http://www.cccfdc.org/"


def test_links():
    assert parsed_items[0]["links"] == [{
        "href":
            "http://www.cccfdc.org/content/pdfs/minutes/2019/1/CCCFDC-Meeting-Minutes-1-25-2019.pdf",  # noqa
        "title": "Minutes"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
