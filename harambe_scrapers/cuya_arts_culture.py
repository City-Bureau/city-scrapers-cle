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

START_URL = "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/"
OUTPUT_DIR = Path("harambe_scrapers/output")
SCRAPER_NAME = "cuya_arts_culture"
AGENCY_NAME = "Cuyahoga County Arts & Culture"
TIMEZONE = "America/New_York"


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    from datetime import datetime

    import pytz
    from dateutil.parser import parse as dateparse

    page: Page = sdk.page

    async def parse_classification(title, description_text):
        title = (title or "").lower()
        description_text = (description_text or "").lower()
        # Define mappings of keywords to classification categories
        classifications = {
            "advisory": "ADVISORY",
            "committee": "COMMITTEE",
            "board": "BOARD",
            "commission": "COMMISION",
            "public meeting": "PUBLIC",
            "policy meeting": "POLICY",
            "community": "COMMUNITY",
            "annual": "ANNUAL",
            "cbo": "CBO",
            "authority": "Authority",
        }
        # First check the title for each keyword
        for keyword, classification in classifications.items():
            if keyword in title or keyword in description_text:
                return classification
        return None

    def convert_to_iso8601(input_datetime_str, target_timezone="America/New_York"):
        # Parse the input datetime string
        naive_datetime = datetime.strptime(str(input_datetime_str), "%Y-%m-%d %H:%M:%S")

        # Add timezone information
        target_tz = pytz.timezone(target_timezone)
        localized_datetime = target_tz.localize(naive_datetime)

        # Format the datetime in ISO 8601 format
        return localized_datetime.isoformat()

    async def fetch_board_materials(page):
        """
        Fetch and parse board materials page.
        """
        await page.goto(
            "https://www.cacgrants.org/about-us/meet-our-board/board-materials/"
        )
        links_dict = {}
        material_elements = await page.query_selector_all(".accordion-body p")

        for element in material_elements:
            meeting_date_str = await element.query_selector("strong")
            if meeting_date_str:
                meeting_date_text = await meeting_date_str.inner_text()
            else:
                continue

            # Extract date using regex
            meeting_date_regex = re.search(
                "[A-Z][a-z]+ \\d{1,2}, \\d{4}", meeting_date_text
            )
            if not meeting_date_regex:
                continue
            meeting_date_str = meeting_date_regex.group()
            meeting_date = dateparse(meeting_date_str)

            links = []
            link_elements = await element.query_selector_all("a")
            for link_element in link_elements:
                title = await link_element.inner_text()
                href = await link_element.get_attribute("href")
                if title and href:
                    links.append({"title": title, "url": page.url + href})

            if links:
                links_dict[meeting_date] = links

        return links_dict

    async def fetch_schedule(page, links_dict):
        """
        Fetch and parse the meeting schedule page.
        """
        await page.goto(
            "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/"
        )
        schedule_elements = await page.query_selector_all(
            ".grid-section .row .column p"
        )

        for element in schedule_elements:
            text_chunks = await element.inner_text()
            clean_chunks = [
                chunk.strip() for chunk in text_chunks.split("\n") if chunk.strip()
            ]

            if len(clean_chunks) < 2:
                continue

            meeting_title = clean_chunks[0]
            meeting_datetime_str = clean_chunks[1]

            # Parse meeting date and time
            meeting_date = parse_meeting_date(meeting_datetime_str)
            if not meeting_date:
                continue
            meeting_time = parse_meeting_time(meeting_datetime_str)
            if not meeting_time:
                continue

            start = datetime.combine(meeting_date, meeting_time)
            meeting_links = links_dict.get(meeting_date, [])

            # Parse location
            location = parse_location(clean_chunks)

            meeting = create_ocd_event(
                title=meeting_title,
                start_time=convert_to_iso8601(start),
                scraper_name=SCRAPER_NAME,
                agency_name=AGENCY_NAME,
                timezone=TIMEZONE,
                description="",
                classification=await parse_classification(meeting_title, ""),
                location=location,
                links=meeting_links,
                end_time=None,
                is_cancelled=True if "cancelled" in meeting_title.lower() else False,
                source_url=START_URL,
            )
            await sdk.save_data(meeting)

    def parse_meeting_date(meeting_datetime_str):
        """
        Extract meeting date from a string in the format "Month DD, YYYY".
        """
        meeting_date_regex = re.search(
            "[A-Z][a-z]+ \\d{1,2}, \\d{4}", meeting_datetime_str
        )
        if not meeting_date_regex:
            return None
        meeting_date_str = meeting_date_regex.group()
        return dateparse(meeting_date_str).date()

    def parse_meeting_time(meeting_datetime_str):
        """
        Extract meeting time from a string like "at 8:30 a.m." or "at 4 p.m.".
        """
        meeting_time_regex = re.search(
            "at (\\d{1,2}(:\\d{2})? [ap]\\.m\\.)", meeting_datetime_str
        )
        if not meeting_time_regex:
            return None
        meeting_time_str = meeting_time_regex.group(1)
        return dateparse(meeting_time_str).time()

    def parse_location(text_chunks):
        """
        Extract location from a list of text chunks.
        """
        default = {"name": None, "address": "TBD"}
        if len(text_chunks) < 3:
            return default

        location_chunks = text_chunks[2:]
        address_pattern = re.compile("[A-Z]{2} \\d{5}")

        for chunk in location_chunks:
            if address_pattern.search(chunk):
                name = " ".join(location_chunks[:-1]).strip()
                return {"name": name, "address": chunk}

        return default

    links_dict = await fetch_board_materials(page)
    await fetch_schedule(page, links_dict)


async def main():
    print("=" * 70)
    print("Cuyahoga County Arts & Culture - Board Meeting Schedule")
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
        fname = f"cuya_arts_culture_{datetime.now():%Y%m%d_%H%M%S}.json"
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
