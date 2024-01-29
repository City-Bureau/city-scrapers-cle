from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import ADVISORY_COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_audit import CuyaAuditSpider

test_response = file_response(
    join(dirname(__file__), "files", "cuya_audit.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/board-details/external/audit-committee",  # noqa
)
test_detail_response = file_response(
    join(dirname(__file__), "files", "cuya_audit_detail.html"),
    url="https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/14/boards-and-commissions/audit-committee-121423",  # noqa
)
spider = CuyaAuditSpider()

freezer = freeze_time("2024-01-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
parsed_item = [item for item in spider._parse_detail(test_detail_response)][0]

freezer.stop()


def test_count():
    assert len(parsed_items) == 4


def test_title():
    assert parsed_item["title"] == "Audit Committee - 12/14/23"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 12, 14, 9, 30)


def test_end():
    assert parsed_item["end"] == datetime(2023, 12, 14, 12, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "cuya_audit/202312140930/x/audit_committee_12_14_23"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {
        "name": "",
        "address": "2079 E. 9th Street, 4th Floor, 4-407 Conference Room B",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://cuyahogacounty.gov/boards-and-commissions/bc-event-detail//2023/12/14/boards-and-commissions/audit-committee-121423"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://cuyahogacms.blob.core.windows.net/home/docs/default-source/boards-and-commissions/external/audit/2023/121423-acagenda.pdf?sfvrsn=76224a31_1",  # noqa
            "title": "Agenda",
        }
    ]


def test_classification():
    assert parsed_item["classification"] == ADVISORY_COMMITTEE


def test_all_day():
    assert parsed_item["all_day"] is False
