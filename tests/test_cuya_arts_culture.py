from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_arts_culture import CuyaArtsCultureSpider

test_materials_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_materials.html"),
    url="https://www.cacgrants.org/about-us/board/board-materials/",
)
test_schedule_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_schedule.html"),
    url="https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/",  # noqa
)

spider = CuyaArtsCultureSpider()

freezer = freeze_time("2024-07-31")
freezer.start()

parsed_materials = next(spider._parse(test_materials_response))
links_dict = parsed_materials.meta["links_dict"]
test_schedule_response.meta["links_dict"] = links_dict.copy()
parsed_meetings = parsed_items = [
    item for item in spider._parse_schedule(test_schedule_response)
]
parsed_meeting = parsed_meetings[0]

freezer.stop()


def test_materials_count():
    assert len(links_dict) == 127


def test_materials_includes_item():
    meeting_datetime = datetime(2024, 2, 15, 0, 0)
    assert meeting_datetime in links_dict


def test_schedule_count():
    assert len(parsed_meetings) == 7


def test_title():
    assert parsed_meeting["title"] == "CAC Board of Trustees Regular Meeting"


def test_description():
    assert parsed_meeting["description"] == ""


def test_start():
    assert parsed_meeting["start"] == datetime(2024, 2, 15, 16, 0)


def test_end():
    assert parsed_meeting["end"] is None


def test_time_notes():
    assert parsed_meeting["time_notes"] == ""


def test_id():
    assert (
        parsed_meeting["id"]
        == "cuya_arts_culture/202402151600/x/cac_board_of_trustees_regular_meeting"  # noqa
    )


def test_status():
    assert parsed_meeting["status"] == PASSED


def test_location():
    assert parsed_meeting["location"] == {
        "name": "Childrens Museum of Cleveland",
        "address": "3813 Euclid Avenue, Cleveland, OH 44115",
    }


def test_source():
    assert (
        parsed_meeting["source"]
        == "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/"  # noqa
    )


def test_links():
    assert parsed_meeting["links"] == [
        {
            "title": "Agenda & Handouts",
            "href": "https://www.cacgrants.org/media/ofpkbzpu/2024-02-15-board-meeting-materials.pdf",  # noqa
        },
        {
            "title": "Minutes",
            "href": "https://www.cacgrants.org/media/yzhhaxqr/20240215-minutes.pdf",  # noqa
        },
    ]


def test_classification():
    assert parsed_meeting["classification"] == BOARD


def test_all_day():
    assert parsed_meeting["all_day"] is False
