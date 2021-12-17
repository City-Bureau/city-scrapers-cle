from datetime import date

import pytest  # noqa

from city_scrapers.utils import calculate_upcoming_meeting_days

start = date(2021, 12, 1)
end = date(2022, 1, 1)


# test a random input - 1 and 3rd tuesday (1)
def test_happy_path():
    expected = [date(2021, 12, 7), date(2021, 12, 21)]

    out = calculate_upcoming_meeting_days(1, [0, 2], start, end)
    assert out == expected


def test_single_day():
    expected = [date(2021, 12, 14)]

    out = calculate_upcoming_meeting_days(1, [1], start, end)
    assert out == expected


def test_multiple_months():
    end = date(2022, 2, 1)
    expected = [
        date(2021, 12, 14),
        date(2021, 12, 28),
        date(2022, 1, 11),
        date(2022, 1, 25),
    ]

    out = calculate_upcoming_meeting_days(1, [1, 3], start, end)
    assert out == expected


def test_start():
    start = date(2021, 12, 8)
    expected = [date(2021, 12, 21)]

    out = calculate_upcoming_meeting_days(1, [0, 2], start, end)
    assert out == expected


def test_start_is_inclusive():
    start = date(2021, 12, 7)
    expected = [date(2021, 12, 7), date(2021, 12, 21)]

    out = calculate_upcoming_meeting_days(1, [0, 2], start, end)
    assert out == expected


def test_end():
    end = date(2021, 12, 20)
    expected = [date(2021, 12, 7)]

    out = calculate_upcoming_meeting_days(1, [0, 2], start, end)
    assert out == expected


def test_end_is_inclusive():
    end = date(2021, 12, 21)
    expected = [date(2021, 12, 7), date(2021, 12, 21)]

    out = calculate_upcoming_meeting_days(1, [0, 2], start, end)
    assert out == expected


def test_all_5():
    expected = [
        date(2021, 12, 1),
        date(2021, 12, 8),
        date(2021, 12, 15),
        date(2021, 12, 22),
        date(2021, 12, 29),
    ]

    out = calculate_upcoming_meeting_days(2, [0, 1, 2, 3, 4], start, end)
    assert out == expected


def test_ordinals_over_4_are_ignored():
    expected = []

    out = calculate_upcoming_meeting_days(1, [5, 6, 7, 8], start, end)
    assert out == expected
