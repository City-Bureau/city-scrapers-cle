import calendar
from datetime import date


def calculate_upcoming_meeting_days(chosen_weekday, chosen_ordinals, start, end):
    """
    Lots of city meeting websites describe their upcoming meetings by saying
    things like: "this committee meets the 1st and 3rd Tuesday of every month ".
    This calculator is intended to help parse dates from such a description.  It
    doesn't handle parsing the actual language, since that might differ from page
    to page, but given a weekday, and a list of the oridnals you care about (like
    1st, 3rd), a start date and an end date, it will return all the meeting dates
    that match the weekday and ordinals.

    Parameters:
    chosen_weekday (int): the weekday that you're looking for. Monday is 0,
        so in the examples above this would be 2
    chosen_ordinals (int[]): the particular days you're looking for - like 1st
        and 3rd. These days should be passed though starting the count from 0,
        i.e [0, 2] for first and third
    start (date): the first day to begin calculating meetings from
    end (date): the final day to be considered as a potential meeting date

    Returns:
    []date: an array of dates that match the given conditions
    """
    current_month = start.month
    current_year = start.year

    raw_dates = []
    while not (current_month == end.month and current_year == end.year):
        current_month_days = _calculate_meeting_days_per_month(
            chosen_weekday, chosen_ordinals, current_year, current_month
        )
        raw_dates = raw_dates + [
            date(current_year, current_month, day) for day in current_month_days
        ]

        # we can't easily use % arithmetic here since we're starting at 1, so
        # it's a bit easier to read this way
        current_month = current_month + 1 if current_month != 12 else 1
        if current_month == 1:
            current_year = current_year + 1

    # add the days for the final month since they're missed by the loop
    current_month_days = _calculate_meeting_days_per_month(
        chosen_weekday, chosen_ordinals, current_year, current_month
    )
    raw_dates = raw_dates + [
        date(current_year, current_month, day) for day in current_month_days
    ]
    # we now have all the relevant dates for the given months but we need to
    # filter out days before and after start and end
    return [
        current_date for current_date in raw_dates if (start <= current_date <= end)
    ]


def _calculate_meeting_days_per_month(chosen_weekday, chosen_ordinals, year, month):
    """
    Lots of city meeting websites describe their upcoming meetings by saying
    things like: "this committee meets the 1st and 3rd Tuesday of every month".
    This calculator is intended to help parse dates from such a description. It
    doesn't handle parsing the actual language, since that might differ from page
    to page, but given a weekday, and a list of the oridnals you care about (like
    1st, 3rd) and a month it will return all the days in the month that match the
    given conditions.

    Parameters:
    chosen_weekday (int): the weekday that you're looking for. Monday is 0, so
        in the examples above this would be 2
    chosen_ordinals (int[]): the particular days you're looking for - like 1st and
        3rd. These days should be passed though starting the count from 0,
        i.e [0, 2] for first and third
    year (int): the year as an integer
    month (int): the month as an integer

    Returns:
    []int: an array of the days of the month that matched the given conditions.
    """

    days_of_the_month = calendar.Calendar().itermonthdays2(year, month)
    # we create a list of all days in the month that are the proper weekday -
    # day is 0 if it is outside the month but present to make complete first or
    # last weeks
    potential_days = [
        day
        for day, weekday in days_of_the_month
        if day != 0 and weekday == chosen_weekday
    ]
    # we then see if the resulting number is in the chosen_weeks array
    chosen_days = [
        day for i, day in enumerate(potential_days) if (i) in chosen_ordinals
    ]

    return chosen_days
