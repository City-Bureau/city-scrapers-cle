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
START_URL = "https://planning.clevelandohio.gov/bza/bbs.html"
OUTPUT_DIR = Path("harambe_scrapers/output")
SCRAPER_NAME = "cle_building_standards_v2"
AGENCY_NAME = "Cleveland Board of Building Standards and Building Appeals"
TIMEZONE = "America/Detroit"


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    from datetime import datetime

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

    def parse_start(value, default_time):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search("\\d{8}", value)
        if not date_match:
            return None
        return datetime.strptime(date_match.group() + default_time, "%m%d%Y%H%M")

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

    page: Page = sdk.page

    # Scroll to the form (if needed)
    form = await page.query_selector('form[name="form2"]')
    if form:
        await form.scroll_into_view_if_needed()

    main_title_el = await page.query_selector(".mb-0.text-danger")
    main_title = await main_title_el.inner_text() if main_title_el else None

    # 1. Extract the time string from the selector
    time_element = await page.query_selector("ul:nth-child(8) li:nth-child(1)")
    if time_element:
        time_text = await time_element.inner_text()
        # 2. Use regex to extract the time (e.g., "9:30 a.m." or "9:30 AM")
        match = re.search(
            "(\\d{1,2}:\\d{2}\\s*[ap]\\.?m\\.?)", time_text, re.IGNORECASE
        )
        if match:
            meeting_time_str = (
                match.group(1).replace(".", "").upper()
            )  # e.g., "9:30 AM"
        else:
            meeting_time_str = "12:00 AM"  # fallback if not found
    else:
        meeting_time_str = "12:00 AM"

    try:
        time_24hr = datetime.strptime(
            meeting_time_str.replace(".", "").upper(), "%I:%M %p"
        ).strftime("%H%M")
    except Exception:
        time_24hr = "0000"  # fallback

    # Get all dropdown items
    dropdown_items = await page.query_selector_all(
        'form[name="form2"] .dropdown-menu a.dropdown-item'
    )
    current_year = str(datetime.now().year)

    for item in dropdown_items:
        link_url = await item.get_attribute("href")
        link_text = await item.inner_text()
        # Try to extract month and day from link_text
        # e.g. "January 15" or "April 23"
        try:
            date_str = f"{link_text} {current_year}"
            # Try parsing with full month name
            try:
                dt = datetime.strptime(date_str, "%B %d %Y")
            except ValueError:
                # Try abbreviated month
                dt = datetime.strptime(date_str, "%b %d %Y")
        except Exception:
            continue

        # Use the extracted meeting_time_str
        try:
            time_obj = datetime.strptime(meeting_time_str, "%I:%M %p")
            dt = dt.replace(hour=time_obj.hour, minute=time_obj.minute)
        except Exception:
            dt = dt.replace(hour=0, minute=0)

        start_time = await change_timezone(dt.strftime("%B-%d-%YT%H:%M:%S"))
        if start_time:
            meeting = create_ocd_event(
                title=main_title,
                start_time=start_time,
                scraper_name=SCRAPER_NAME,
                agency_name=AGENCY_NAME,
                timezone=TIMEZONE,
                description="",
                classification=await parse_classification(main_title),
                location={
                    "address": (
                        "https://www.youtube.com/channel/" "UCB8ql0Jrhm_pYIR1OLY68bw/"
                    ),
                    "name": "live streamed on YouTube",
                },
                links=[
                    {
                        "url": f"http://planning.city.cleveland.oh.us{link_url}",
                        "title": "Agenda",
                    }
                ],
                end_time=None,
                is_cancelled=False,
                source_url=START_URL,
            )
            await sdk.save_data(meeting)

    # For different years when they're available on the page:

    year_elements = await page.query_selector_all("select#ID option")
    years = []
    for year_element in year_elements:
        years.append(await year_element.get_attribute("value"))

    for year in years:
        url = f"https://planning.city.cleveland.oh.us/bza/bbs.html?ID={year}"

        location = None
        await page.goto(url)

        # Validate location
        content = await page.content()
        if "516" not in content:
            raise ValueError("Meeting location has changed")
        main_title_el = await page.query_selector(".mb-0.text-danger")
        main_title = await main_title_el.inner_text() if main_title_el else None

        options = await page.locator("#jumpMenu option").all()

        for option in options:
            value = await option.get_attribute("value")
            if not value:
                continue

            start = parse_start(value, time_24hr)
            if not start:
                continue

            link = {"url": f"{url}{value}", "title": "Agenda"}

            meeting = create_ocd_event(
                title=main_title,
                start_time=await change_timezone(start.isoformat()),
                scraper_name=SCRAPER_NAME,
                agency_name=AGENCY_NAME,
                timezone=TIMEZONE,
                description="",
                classification=await parse_classification(main_title),
                location=location,
                links=[link],
                end_time=None,
                is_cancelled=False,
                source_url=START_URL,
            )
            await sdk.save_data(meeting)


async def main():
    print("=" * 70)
    print("Cleveland Board of Building Standards and Building Appeals")
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
        fname = f"cle_building_standards_v2_{datetime.now():%Y%m%d_%H%M%S}.json"
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
