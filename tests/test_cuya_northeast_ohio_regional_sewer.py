from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_northeast_ohio_regional_sewer import (
    CuyaNortheastOhioRegionalSewerSpider
)

test_response = file_response(
    join(dirname(__file__), "files", "cuya_northeast_ohio_regional_sewer.html"),
    url=(
        "https://www.neorsd.org/document-library/?PAGE=2&BUDGETCENTER_ID=NULL&CONTENT_TYPE_ID=NULL&LibraryItem=agenda&Active=1&Archive=1&Search=Submit"  # noqa
    ),
)
spider = CuyaNortheastOhioRegionalSewerSpider()

freezer = freeze_time("2019-09-16")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 7


def test_title():
    assert parsed_items[0]["title"] == "Board of Trustees"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2019, 6, 20, 12, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == "See documents to confirm details"


def test_id():
    assert parsed_items[0][
        "id"] == "cuya_northeast_ohio_regional_sewer/201906201230/x/board_of_trustees"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == spider.location


def test_source():
    assert parsed_items[0][
        "source"
    ] == "https://www.neorsd.org/document-library/?PAGE=2&BUDGETCENTER_ID=NULL&CONTENT_TYPE_ID=NULL&LibraryItem=agenda&Active=1&Archive=1&Search=Submit"  # noqa


def test_links():
    assert parsed_items[0]["links"] == [{
        "href":
            "https://www.neorsd.org/I_Library.php?SOURCE=library/BA-062019.pdf&a=download_file&LIBRARY_RECORD_ID=7463",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
