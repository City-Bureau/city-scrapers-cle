from collections import defaultdict
from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_health import CuyaHealthSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_health.html"),
    url="https://www.ccbh.net/board-minutes-agenda/",
)
test_pdf_response = file_response(
    join(dirname(__file__), "files", "cuya_health.pdf"),
    url="https://www.ccbh.net/wp-content/uploads/2019/04/REVISED-April-2019-Board-Agenda.pdf",  # noqa
    mode="rb",
)
spider = CuyaHealthSpider()

freezer = freeze_time("2019-10-21")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
spider.link_date_map = defaultdict(list)
spider._parse_pdf(test_pdf_response)
parsed_item = [item for item in spider._yield_meetings(test_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 41


def test_title():
    assert parsed_item["title"] == "Board of Health"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 4, 24, 9, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == "Confirm details with agency"


def test_id():
    assert parsed_item["id"] == "cuya_health/201904240900/x/board_of_health"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == test_response.url


def test_links():
    assert parsed_item["links"] == [{"href": test_pdf_response.url, "title": "Agenda"}]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
