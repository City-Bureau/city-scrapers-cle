from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_metrohealth import CuyaMetrohealthSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_metrohealth.html"),
    url="https://www.metrohealth.org/about-us/board-and-governance/meetings",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_metrohealth_detail.html"),
    url="https://www.metrohealth.org/about-us/board-and-governance/meetings/07-2024",  # noqa
)
spider = CuyaMetrohealthSpider()

freezer = freeze_time("2024-07-15")  # Adjusted date for context
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = next(spider._parse_detail(test_detail_response))

freezer.stop()


def test_count():
    assert len(parsed_items) == 7  # Assuming actual item count from `parse`


def test_title():
    assert parsed_item["title"] == "Board of Trustees"


def test_description():
    text_frag = "Wednesday, July 31, 2024 Special Meeting - The purpose of this meeting is to approve the Internal Audit plan."  # noqa
    assert text_frag in parsed_item["description"]


def test_start():
    assert parsed_item["start"] == datetime(2024, 7, 31, 0, 0)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"] == "cuya_metrohealth/202407310000/x/board_of_trustees"
    )  # noqa


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "MetroHealth Business Services Building, Board Room K-107",
        "address": "2500 MetroHealth Dr, Cleveland, OH 44109",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.metrohealth.org/about-us/board-and-governance/meetings/07-2024"  # noqa
    )


def test_links():
    # Assuming there are no specific links provided for this test case
    assert parsed_item["links"] == []


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
