"""
Tests for the Cuyahoga County Arts & Culture spider.

These tests verify the spider's ability to:
1. Parse meeting materials from the board materials page
2. Parse meeting schedules from the board schedule page
3. Combine the information into complete meeting records

The tests use static HTML files captured from the actual website,
with a frozen timestamp of July 31, 2024 for consistent testing.
"""

from datetime import datetime
from os.path import dirname, join

import pytest  # noqa
from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.cuya_arts_culture import CuyaArtsCultureSpider

# Load test data from static HTML files
test_materials_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_materials.html"),
    url="https://www.cacgrants.org/about-us/board/board-materials/",
)
test_schedule_response = file_response(
    join(dirname(__file__), "files", "cuya_arts_culture_schedule.html"),
    url="https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/",
)

# Initialize spider and parse test data
spider = CuyaArtsCultureSpider()

# Freeze time to ensure consistent test results
freezer = freeze_time("2024-07-31")
freezer.start()

# Parse materials and schedule pages
parsed_materials = next(spider._parse(test_materials_response))
links_dict = parsed_materials.meta["links_dict"]
test_schedule_response.meta["links_dict"] = links_dict.copy()
parsed_meetings = [
    item for item in spider._parse_schedule(test_schedule_response)
]
parsed_meeting = parsed_meetings[0]  # Use first meeting for individual field tests

freezer.stop()


# Test meeting materials parsing
def test_materials_count():
    """Verify the correct number of meeting materials were parsed."""
    assert len(links_dict) == 127


def test_materials_includes_item():
    """Verify specific meeting materials can be found by date."""
    meeting_datetime = datetime(2024, 2, 15, 0, 0)
    assert meeting_datetime in links_dict, "Expected meeting materials not found"


def test_schedule_count():
    """Verify the correct number of scheduled meetings were parsed."""
    assert len(parsed_meetings) == 7, "Expected 7 upcoming meetings"


# Test individual meeting field parsing
def test_title():
    """Verify correct parsing of meeting title."""
    assert parsed_meeting["title"] == "CAC Board of Trustees Regular Meeting"


def test_description():
    """Verify meeting description (empty in this case)."""
    assert parsed_meeting["description"] == ""


def test_start():
    """Verify correct parsing of meeting start time."""
    expected_start = datetime(2024, 2, 15, 16, 0)  # 4:00 PM
    assert parsed_meeting["start"] == expected_start


def test_end():
    """Verify meeting end time (None in this case)."""
    assert parsed_meeting["end"] is None, "End time should not be set"


def test_time_notes():
    """Verify time-related notes (empty in this case)."""
    assert parsed_meeting["time_notes"] == ""


def test_id():
    """Verify correct generation of meeting ID."""
    expected_id = "cuya_arts_culture/202402151600/x/cac_board_of_trustees_regular_meeting"
    assert parsed_meeting["id"] == expected_id


def test_status():
    """Verify correct meeting status (PASSED due to frozen time)."""
    assert parsed_meeting["status"] == PASSED, "Meeting should be marked as passed"


def test_location():
    """Verify correct parsing of meeting location."""
    expected_location = {
        "name": "Childrens Museum of Cleveland",
        "address": "3813 Euclid Avenue, Cleveland, OH 44115",
    }
    assert parsed_meeting["location"] == expected_location


def test_source():
    """Verify correct source URL for meeting information."""
    expected_url = "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/"
    assert parsed_meeting["source"] == expected_url


def test_links():
    """
    Verify correct parsing of meeting-related document links.
    
    Tests both agenda/handouts and minutes links are correctly extracted
    and formatted with proper titles and absolute URLs.
    """
    expected_links = [
        {
            "title": "Agenda & Handouts",
            "href": "https://www.cacgrants.org/media/ofpkbzpu/2024-02-15-board-meeting-materials.pdf",
        },
        {
            "title": "Minutes",
            "href": "https://www.cacgrants.org/media/aqxpxwxm/2024-02-15-board-meeting-minutes.pdf",
        },
    ]
    assert parsed_meeting["links"] == expected_links, "Meeting links do not match expected format"


def test_classification():
    """
    Verify meeting classification is set to BOARD.
    
    All meetings from this spider should be classified as board meetings
    as they are meetings of the Board of Trustees.
    """
    assert parsed_meeting["classification"] == BOARD, "Meeting should be classified as BOARD"


def test_all_day():
    assert parsed_meeting["all_day"] is False
