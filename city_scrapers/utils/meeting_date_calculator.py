import calendar
from datetime import date


def calculate_upcoming_meeting_days(chosen_weekday, chosen_ordinals, start, end):
    """
    Calculate meeting dates that fall on specified weekdays and ordinals within a date range.
    
    Parameters:
    chosen_weekday (int): Weekday (0=Monday, 6=Sunday)
    chosen_ordinals (int[]): List of ordinals (0-based) like [0,2] for 1st and 3rd
    start (date): Start date
    end (date): End date
    
    Returns:
    []date: List of matching meeting dates
    """
    # Filter out invalid ordinals (5 or greater)
    valid_ordinals = [ord for ord in chosen_ordinals if ord < 5]
    if not valid_ordinals:
        return []
        
    result = []
    current = date(start.year, start.month, 1)
    
    while current <= end:
        days = _calculate_meeting_days_per_month(
            chosen_weekday, valid_ordinals, current.year, current.month
        )
        
        for day in days:
            meeting_date = date(current.year, current.month, day)
            if start <= meeting_date <= end:
                result.append(meeting_date)
        
        # Move to first day of next month
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        current = date(year, month, 1)
            
    return result


def _calculate_meeting_days_per_month(chosen_weekday, chosen_ordinals, year, month):
    """
    Calculate days of the month that match given weekday and ordinal criteria.
    
    Parameters:
    chosen_weekday (int): Weekday (0=Monday, 6=Sunday)
    chosen_ordinals (int[]): List of ordinals (0-based) like [0,2] for 1st and 3rd
    year (int): Year
    month (int): Month
    
    Returns:
    []int: List of matching days of the month
    """
    # Get first day of month and its weekday
    first_day_weekday = calendar.weekday(year, month, 1)
    
    # Calculate first occurrence of chosen weekday
    first_occurrence = 1 + ((chosen_weekday - first_day_weekday) % 7)
    if first_occurrence <= 0:
        first_occurrence += 7
        
    # Calculate all occurrences
    last_day = calendar.monthrange(year, month)[1]
    result = []
    
    for ordinal in chosen_ordinals:
        day = first_occurrence + (ordinal * 7)
        if day <= last_day:
            result.append(day)
            
    return result
