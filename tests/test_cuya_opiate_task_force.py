from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import COMMISSION, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_opiate_task_force import CuyaOpiateTaskForceSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_opiate_task_force.html"),
    url="http://opiatecollaborative.cuyahogacounty.us/en-US/Meeting-Calendar.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_opiate_task_force_detail.html"),
    url="http://opiatecollaborative.cuyahogacounty.us/en-US/101519-Opiate-Task-Force-meeting.aspx",
)
spider = CuyaOpiateTaskForceSpider()

freezer = freeze_time("2019-10-05")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 1


def test_title():
    assert parsed_item["title"] == "Opiate Task Force"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 10, 15, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2019, 10, 15, 10, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_opiate_task_force/201910150900/x/opiate_task_force"


def test_status():
    assert parsed_item["status"] == TENTATIVE


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == test_detail_response.url


def test_links():
    assert parsed_item["links"] == [{
        "href":
            "http://opiatecollaborative.cuyahogacounty.us/ViewFile.aspx?file=0fXU2JOpNknBfOHqKZmC3Q%3d%3d",  # noqa
        "title": "Agenda"
    }]


def test_classification():
    assert parsed_item["classification"] == COMMISSION


def test_all_day():
    assert parsed_item["all_day"] is False
