from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_board_control import CuyaBoardControlSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_board_control.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/board-of-control",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_board_control_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/29/boards-and-commissions/01-29-24---board-of-control-meeting",  # noqa
)
spider = CuyaBoardControlSpider()

freezer = freeze_time("2024-01-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 5


def test_title():
    assert parsed_item["title"] == "01/29/24 - Board of Control Meeting"


def test_description():
    assert (
        parsed_item["description"]
        == "This meeting is open to the public and may also be accessed via livestream using the following link: https://www.YouTube.com/CuyahogaCounty"  # noqa
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 29, 11, 0)


def test_end():
    assert parsed_item["end"] == datetime(2024, 1, 29, 12, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_board_control/202401291100/x/01_29_24_board_of_control_meeting"
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "County Headquarters 2079 East Ninth Street 4th, Cmmt Room B",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/29/boards-and-commissions/01-29-24---board-of-control-meeting"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/boc/2024/012924-bocagenda.pdf?sfvrsn=60356a8a_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
