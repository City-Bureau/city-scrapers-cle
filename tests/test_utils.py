"""
Unit tests for shared utility functions used across scrapers.
"""

from datetime import datetime, timedelta

import pytz

from harambe_scrapers.utils import (
    determine_status,
    generate_id,
    generate_ocd_id,
    slugify,
)


def test_slugify():
    """Test slugify function with various inputs"""
    assert slugify("Board Meeting") == "board_meeting"
    assert slugify("Meeting #123") == "meeting_123"
    assert slugify("   Spaces   ") == "spaces"
    assert slugify("Special-Characters!@#") == "special-characters"
    assert slugify("Multiple   Spaces") == "multiple_spaces"
    assert slugify("under_score") == "under_score"
    assert slugify("") == ""
    assert slugify("CAPS-and-lower") == "caps-and-lower"
    assert slugify("123-numbers") == "123-numbers"


def test_slugify_edge_cases():
    """Test slugify with edge cases"""
    assert slugify(None) == "none"
    assert slugify(123) == "123"
    assert slugify("---test---") == "test"
    assert slugify("___test___") == "_test_"
    assert slugify("test-") == "test"
    assert slugify("-test") == "test"


def test_generate_id():
    """Test ID generation"""
    scraper_name = "test_scraper"

    # Normal meeting
    result = generate_id("Board Meeting", "2025-01-15T09:00:00-05:00", scraper_name)
    assert result == f"{scraper_name}/202501150900/x/board_meeting"

    # Complex name with hyphens
    result = generate_id(
        "Board of Trustees - Special Meeting #123",
        "2025-12-31T23:59:00-05:00",
        scraper_name,
    )
    assert (
        result
        == f"{scraper_name}/202512312359/x/board_of_trustees_-_special_meeting_123"
    )

    # UTC timezone
    result = generate_id("Test Meeting", "2025-01-15T14:00:00Z", scraper_name)
    assert result == f"{scraper_name}/202501151400/x/test_meeting"


def test_generate_ocd_id():
    """Test OCD ID generation"""
    scraper_id = "test_scraper/202501150900/x/board_meeting"
    result = generate_ocd_id(scraper_id)

    # Verify format
    assert result.startswith("ocd-event/")
    parts = result.replace("ocd-event/", "").split("-")
    assert len(parts) == 5
    assert len(parts[0]) == 8  # First segment
    assert len(parts[1]) == 4  # Second segment
    assert len(parts[2]) == 4  # Third segment
    assert len(parts[3]) == 4  # Fourth segment
    assert len(parts[4]) == 12  # Fifth segment

    # Verify deterministic - same input always produces same output
    result2 = generate_ocd_id(scraper_id)
    assert result == result2

    # Different input produces different output
    different_id = "test_scraper/202501160900/x/different_meeting"
    result3 = generate_ocd_id(different_id)
    assert result3 != result


def test_determine_status():
    """Test status determination"""
    tz = pytz.timezone("America/Detroit")
    now = datetime.now(tz)

    future_time = (now + timedelta(days=7)).isoformat()
    past_time = (now - timedelta(days=7)).isoformat()
    current_time = now.isoformat()

    assert determine_status(True, future_time) == "canceled"
    assert determine_status(True, past_time) == "canceled"
    assert determine_status(True, current_time) == "canceled"

    assert determine_status(False, future_time) == "tentative"

    assert determine_status(False, past_time) == "passed"
    assert determine_status(False, current_time) == "passed"
