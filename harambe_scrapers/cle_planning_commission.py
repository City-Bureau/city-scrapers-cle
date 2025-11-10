import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from harambe import SDK
from harambe.contrib import playwright_harness
from playwright.async_api import Page

from harambe_scrapers.observers import DataCollector
from harambe_scrapers.utils import create_ocd_event

# Configuration
START_URL = "https://planning.clevelandohio.gov/designreview/schedule.php"
OUTPUT_DIR = Path("harambe_scrapers/output")
SCRAPER_NAME = "cle_planning_commission_v2"
AGENCY_NAME = "Cleveland City Planning Commission"
TIMEZONE = "America/Detroit"


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    from datetime import datetime, timedelta

    import pytz

    async def change_timezone(date):
        timezone = "America/Detroit"

        # Normalize the date string
        # List of possible formats
        # Format with full month name (e.g., December)
        # Format with numeric month
        # Format with day first
        # Default format
        date_formats = [
            "%B-%d-%YT%H:%M:%S",
            "%m-%d-%YT%H:%M:%S",
            "%d-%m-%YT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        # Try parsing the date with different formats
        naive_datetime = None
        for date_format in date_formats:
            try:
                naive_datetime = datetime.strptime(date, date_format)
                break  # Stop on successful parsing
            except ValueError:
                continue

        if not naive_datetime:
            print(f"Invalid date format: {date}")
            return None

        # Get the timezone object
        tz = pytz.timezone(timezone)

        # Add timezone to the naive datetime
        localized_datetime = tz.localize(naive_datetime)

        # Format the localized datetime as ISO 8601 string
        iso_format = localized_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Adjusting the offset format to include a colon
        iso_format_with_colon = iso_format[:-2] + ":" + iso_format[-2:]

        return iso_format_with_colon

    async def parse_classification(title):
        title = (title or "").lower()

        # Define mappings of keywords to classification categories
        classifications = {
            "committee": "COMMITTEE",
            "board": "BOARD",
            "commission": "COMMISION",
            "public meeting": "PUBLIC",
            "policy meeting": "POLICY",
            "community": "COMMUNITY",
            "annual": "ANNUAL",
            "cbo": "CBO",
            "advisory": "ADVISORY",
            "council": "COUNCIL",
        }

        # First check the title for each keyword
        for keyword, classification in classifications.items():
            if keyword in title:
                return classification

        return None

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
            day for i, day in enumerate(potential_days) if i in chosen_ordinals
        ]

        return chosen_days

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
            current_date for current_date in raw_dates if start <= current_date <= end
        ]

    def validate_schedule(text):
        if "every 1st & 3rd Friday" not in text:
            raise ValueError("Meeting schedule has changed")

    def parse_start(year_str, month_str, day_str, time_str):
        date_str = " ".join([year_str, month_str[:3], day_str, time_str])
        return datetime.strptime(date_str, "%Y %b %d %I:%M%p")

    def parse_calculated_start(day, time_str):
        date_str = " ".join([day.strftime("%Y %B %d"), time_str])
        return datetime.strptime(date_str, "%Y %B %d %I:%M%p")

    async def parse_links(agenda, presentations, page):
        links = [
            {
                "title": "Agenda",
                "url": await page.evaluate("(item) => item.href", agenda),
            }
        ]
        key = await dropdown_to_key(agenda)
        if key in presentations:
            links.append(
                {
                    "title": "Presentation",
                    "url": "https://planning.clevelandohio.gov" + presentations[key],
                }
            )
        return links

    async def parse_year_from_link(item):
        link = await item.get_attribute("href")
        year_match = re.search("/(20\\d{2})/", link)
        if year_match:
            return year_match.group(1)
        return str(datetime.today().year)

    async def parse_presentations(items):
        presentations = {}
        presentation_items = await items.query_selector_all(
            "div.dropdown-menu a.dropdown-item"
        )
        for presentation in presentation_items:
            key = await dropdown_to_key(presentation)
            href = await presentation.get_attribute("href")
            presentations[key] = href
        return presentations

    async def dropdown_to_key(item):
        text = await item.text_content()
        month_str, day_str = text.strip().split(" ")[:2]
        year = await parse_year_from_link(item)
        if int(day_str) < 10:
            day_str = "0" + str(day_str) if "0" != day_str[0] else day_str
        return f"{year}-{month_str}-{day_str}"

    location_page = "https://planning.clevelandohio.gov/landmark/cpc.html"
    start_url = "https://planning.clevelandohio.gov/designreview/schedule.php"

    page: Page = sdk.page
    await page.goto(location_page)
    await page.wait_for_selector(".body3")
    location_element = await page.query_selector(".body3")
    location_text = await location_element.inner_text()
    if location_text:
        default_location_text = location_text.split("Phone")[0].split("Email")[0]
    else:
        default_location_text = None
    await page.goto(start_url)

    most_recent_start = datetime.today()

    title_el = await page.query_selector(".mb-2.mt-2")
    main_title = await title_el.inner_text() if title_el else None
    time_loc_el = await page.query_selector(".text-center.mb-0")
    time_loc_text = await time_loc_el.inner_text() if time_loc_el else None
    d_time = (
        time_loc_text.split("at")[1].split(",")[0].replace(" ", "")
        if time_loc_text
        else None
    )
    time_str = d_time if d_time else ""
    d_loc = time_loc_text.split(" in ")[1].split(",") if time_loc_text else None
    location = (
        {
            "address": d_loc[0] if len(d_loc) > 1 else d_loc,
            "name": d_loc[1] if len(d_loc) > 1 else "",
        }
        if d_loc
        else None
    )
    if (
        default_location_text
        and location
        and ("City Hall" in location["name"] and "Room" in location["address"])
    ):
        pattern = "Room \\d+"
        match = re.search(pattern, default_location_text)
        if match:
            default_location_text = re.sub(
                pattern, location["address"], default_location_text
            )
            location["address"] = default_location_text
        else:
            location["address"] = location["address"] + " " + default_location_text
    elif not location and "Virtual" in time_loc_text:
        location = {"name": "Virtual", "address": ""}
    elif default_location_text and (not location):
        location = {"name": "", "address": default_location_text}

    classification = await parse_classification(main_title)

    dropdowns = await page.query_selector_all(
        "div.container div.container div.container div.dropdown"
    )
    commission_agendas = dropdowns[0]
    commission_presentations = await parse_presentations(dropdowns[1])

    agenda_items = await commission_agendas.query_selector_all(
        "div.dropdown-menu a.dropdown-item"
    )
    for agenda in agenda_items:
        agenda_text = await agenda.text_content()
        month_str, day_str = agenda_text.strip().split(" ")[:2]
        year_str = await parse_year_from_link(agenda)

        start = parse_start(year_str, month_str, day_str, time_str)
        most_recent_start = max(most_recent_start, start)

        if start:
            meeting = create_ocd_event(
                title=main_title,
                start_time=await change_timezone(start.isoformat()),
                scraper_name=SCRAPER_NAME,
                agency_name=AGENCY_NAME,
                timezone=TIMEZONE,
                description="",
                classification=classification,
                location=location,
                links=await parse_links(agenda, commission_presentations, page),
                end_time=None,
                is_cancelled=True if "cancel" in main_title.lower() else False,
                source_url=START_URL,
            )
            await sdk.save_data(meeting)

    calc_start = most_recent_start + timedelta(days=1)
    calc_end = calc_start + timedelta(days=185)  # over 6 months
    upcoming_meetings = calculate_upcoming_meeting_days(
        4, [0, 2], calc_start.date(), calc_end.date()
    )

    for day in upcoming_meetings:
        start = parse_calculated_start(day, time_str)
        meeting = create_ocd_event(
            title=main_title,
            start_time=await change_timezone(start.isoformat()),
            scraper_name=SCRAPER_NAME,
            agency_name=AGENCY_NAME,
            timezone=TIMEZONE,
            description="",
            classification=classification,
            location=location,
            links=[],
            end_time=None,
            is_cancelled=True if "cancel" in main_title.lower() else False,
            source_url=START_URL,
        )
        await sdk.save_data(meeting)


async def main():
    print("=" * 70)
    print("Cleveland City Planning Commission")
    print("=" * 70)
    print()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Scraping: {START_URL}")
    print()

    observer = DataCollector(scraper_name=SCRAPER_NAME, timezone=TIMEZONE)

    try:
        await SDK.run(
            scrape,
            START_URL,
            observer=observer,
            harness=playwright_harness,
            headless=True,
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 70)
    print(f"COMPLETE: {len(observer.data)} meetings collected")
    print("=" * 70)

    if observer.data:
        fname = f"cle_planning_commission_v2_{datetime.now():%Y%m%d_%H%M%S}.json"
        output_file = OUTPUT_DIR / fname
        # Write JSONLINES format - one JSON object per line
        with open(output_file, "w") as f:
            for meeting in observer.data:
                # Remove __url field if it exists (added by Harambe SDK)
                if "__url" in meeting:
                    del meeting["__url"]
                f.write(json.dumps(meeting, ensure_ascii=False) + "\n")

        print(f"✓ Saved local backup to: {output_file}")

        if observer.azure_client:
            print(f"✓ Uploaded {len(observer.data)} meetings to Azure Blob Storage")

        print()
        print("Sample meeting:")
        print("-" * 70)
        print(json.dumps(observer.data[0], indent=2))
    else:
        print("⚠ No meetings collected")


if __name__ == "__main__":
    asyncio.run(main())
