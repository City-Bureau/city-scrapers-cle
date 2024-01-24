from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_board_revision import CuyaBoardRevisionSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_board_revision.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/internal/board-of-revision",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_board_revision_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/08/boards-and-commissions/bor-organizational-meeting---010824",  # noqa
)
spider = CuyaBoardRevisionSpider()

freezer = freeze_time("2024-01-05")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "BOR Organizational Meeting - 01/08/2024"


def test_description():
    assert (
        parsed_item["description"]
        == "Pursuant to ORC 5715.09, the Cuyahoga County Board of Revision is conducting the Annual Organizational Meeting on Monday, January 8, 2023, at 10:15 AM. The meeting will take place at the Cuyahoga County Administrative Headquarters, 2079 East Ninth Street, Cleveland, OH 44115 in Room 2-101 (Board Room G). This meeting is open to the public for both in-person and virtual attendance. If you would like to attend virtually, the Zoom link will be posted on the Board of Revision website 15 minutes prior to the start of the meeting.  For more information, please see the meeting agenda."  # noqa
    )


def test_start():
    assert parsed_item["start"] == datetime(2024, 1, 8, 10, 15)


def test_end():
    assert parsed_item["end"] == datetime(2024, 1, 8, 11, 15)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert (
        parsed_item["id"]
        == "cuya_board_revision/202401081015/x/bor_organizational_meeting_01_08_2024"  # noqa
    )


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 East 9th Street, Room 2-101 (Board Room G)",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2024/01/08/boards-and-commissions/bor-organizational-meeting---010824"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/bor/2023/010824-boragenda.pdf?sfvrsn=59466488_1",  # noqa
            "title": "Agenda",
        },
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/internal/bor/2024/010824-borminutes.pdf?sfvrsn=6cf1909f_1",  # noqa
            "title": "Minutes",
        },
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
