"""
Tests for the meeting date calculator utility.

These tests verify the functionality of calculate_upcoming_meeting_days,
which generates meeting dates based on weekday and ordinal criteria
(e.g., "1st and 3rd Tuesday of each month").

Common test parameters:
    weekday: Integer 0-6 (Monday=0, Sunday=6)
    ordinals: List of integers (0=1st, 1=2nd, etc.)
    start_date: Beginning of date range
    end_date: End of date range
"""

from datetime import date

import pytest  # noqa

from city_scrapers.utils import calculate_upcoming_meeting_days

# Default date range for most tests
DEFAULT_START = date(2021, 12, 1)  # December 1, 2021
DEFAULT_END = date(2022, 1, 1)    # January 1, 2022


def test_happy_path():
    """
    Test basic functionality with 1st and 3rd Tuesdays.
    
    Scenario: Meetings on 1st and 3rd Tuesday of December 2021
    Expected: December 7 (1st Tuesday) and December 21 (3rd Tuesday)
    """
    expected = [date(2021, 12, 7), date(2021, 12, 21)]
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[0, 2],  # 1st and 3rd
        start=DEFAULT_START,
        end=DEFAULT_END
    )
    assert result == expected


def test_single_day():
    """
    Test with a single ordinal (2nd Tuesday only).
    
    Scenario: Meetings only on 2nd Tuesday of December 2021
    Expected: December 14 only
    """
    expected = [date(2021, 12, 14)]
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[1],  # 2nd only
        start=DEFAULT_START,
        end=DEFAULT_END
    )
    assert result == expected


def test_multiple_months():
    """
    Test date calculation across multiple months.
    
    Scenario: Meetings on 2nd and 4th Tuesdays from Dec 2021 through Jan 2022
    Expected: Dec 14, Dec 28, Jan 11, Jan 25
    """
    extended_end = date(2022, 2, 1)  # Extend to February 1st
    expected = [
        date(2021, 12, 14),  # 2nd Tuesday of December
        date(2021, 12, 28),  # 4th Tuesday of December
        date(2022, 1, 11),   # 2nd Tuesday of January
        date(2022, 1, 25),   # 4th Tuesday of January
    ]
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[1, 3],  # 2nd and 4th
        start=DEFAULT_START,
        end=extended_end
    )
    assert result == expected


def test_start():
    """
    Test that meetings before start date are excluded.
    
    Scenario: Start date falls after first meeting of month
    Expected: Only meetings after start date should be included
    """
    custom_start = date(2021, 12, 8)  # After first Tuesday
    expected = [date(2021, 12, 21)]   # Only third Tuesday included
    
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[0, 2],  # 1st and 3rd
        start=custom_start,
        end=DEFAULT_END
    )
    assert result == expected


def test_start_is_inclusive():
    """
    Test that meetings on the start date are included.
    
    Scenario: Start date falls exactly on a meeting date
    Expected: That meeting and subsequent meetings should be included
    """
    custom_start = date(2021, 12, 7)  # First Tuesday
    expected = [
        date(2021, 12, 7),   # First Tuesday (start date)
        date(2021, 12, 21)   # Third Tuesday
    ]
    
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[0, 2],  # 1st and 3rd
        start=custom_start,
        end=DEFAULT_END
    )
    assert result == expected


def test_end():
    """
    Test that meetings after end date are excluded.
    
    Scenario: End date falls before last meeting of month
    Expected: Only meetings before end date should be included
    """
    custom_end = date(2021, 12, 20)  # Before third Tuesday
    expected = [date(2021, 12, 7)]   # Only first Tuesday included
    
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[0, 2],  # 1st and 3rd
        start=DEFAULT_START,
        end=custom_end
    )
    assert result == expected


def test_end_is_inclusive():
    """
    Test that meetings on the end date are included.
    
    Scenario: End date falls exactly on a meeting date
    Expected: That meeting and prior meetings should be included
    """
    custom_end = date(2021, 12, 21)  # Third Tuesday
    expected = [
        date(2021, 12, 7),   # First Tuesday
        date(2021, 12, 21)   # Third Tuesday (end date)
    ]
    
    result = calculate_upcoming_meeting_days(
        weekday=1,           # Tuesday
        chosen_ordinals=[0, 2],  # 1st and 3rd
        start=DEFAULT_START,
        end=custom_end
    )
    assert result == expected


def test_all_5():
    """
    Test with all possible ordinals in a month.
    
    Scenario: Meetings every Wednesday in December 2021
    Expected: All five Wednesdays in December should be included
    """
    expected = [
        date(2021, 12, 1),   # 1st Wednesday
        date(2021, 12, 8),   # 2nd Wednesday
        date(2021, 12, 15),  # 3rd Wednesday
        date(2021, 12, 22),  # 4th Wednesday
        date(2021, 12, 29),  # 5th Wednesday
    ]
    
    result = calculate_upcoming_meeting_days(
        weekday=2,                    # Wednesday
        chosen_ordinals=[0,1,2,3,4],  # All possible ordinals
        start=DEFAULT_START,
        end=DEFAULT_END
    )
    assert result == expected


def test_ordinals_over_4_are_ignored():
    """
    Test that invalid ordinals (5 or greater) are ignored.
    
    Scenario: Only invalid ordinals provided (5th-8th)
    Expected: No meetings should be returned
    Note: A month can never have more than 5 occurrences of a weekday
    """
    result = calculate_upcoming_meeting_days(
        weekday=1,               # Tuesday
        chosen_ordinals=[5,6,7,8],  # All invalid
        start=DEFAULT_START,
        end=DEFAULT_END
    )
    assert result == []
