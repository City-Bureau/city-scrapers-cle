from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_administrative_rules import CuyaAdministrativeRulesSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_administrative_rules.html"),
    url="http://arb.cuyahogacounty.us/en-US/events-calendar.aspx",
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_administrative_rules_detail.html"),
    url="http://arb.cuyahogacounty.us/en-US/061319-meeting.aspx",
)
spider = CuyaAdministrativeRulesSpider()

freezer = freeze_time("2019-09-17")
freezer.start()

parsed_items = [item for item in spider._parse_form_response(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 0


def test_title():
    assert parsed_item["title"] == "Administrative Rules Board"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2019, 6, 13, 9, 30)


def test_end():
    assert parsed_item["end"] == datetime(2019, 6, 13, 11, 30)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"
                       ] == "cuya_administrative_rules/201906130930/x/administrative_rules_board"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == spider.location


def test_source():
    assert parsed_item["source"] == "http://arb.cuyahogacounty.us/en-US/061319-meeting.aspx"


def test_links():
    assert parsed_item["links"] == [{
        "href": "http://arb.cuyahogacounty.us/ViewFile.aspx?file=k4UvRH5p4l98sj%2bKnczirQ%3d%3d",
        "title": "Agenda"
    }, {
        "href": "http://arb.cuyahogacounty.us/ViewFile.aspx?file=Qa7DoYdtpmbKy%2f4k1H26og%3d%3d",
        "title": "Minutes"
    }, {
        "href": "http://arb.cuyahogacounty.us/pdf_arb/en-US/ScooterSharePresentation.pdf",
        "title": "Scooter Share Presentation"
    }, {
        "href": "http://arb.cuyahogacounty.us/pdf_arb/en-US/BirdComments.pdf",
        "title": "Letter from Sam Cooper"
    }, {
        "href": "http://arb.cuyahogacounty.us/pdf_arb/en-US/LIMELetter.pdf",
        "title": "Letter from LIME"
    }]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
