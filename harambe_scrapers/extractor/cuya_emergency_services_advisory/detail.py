import asyncio
import re
from typing import Any

from harambe import SDK
from harambe.contrib import playwright_harness
from playwright.async_api import Page, TimeoutError


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

    async def extract_and_format_date(original_datetime_str, date_time):
        # Normalize whitespace
        # Split by ' - ' to separate start and end times
        parts = date_time.split(" - ")
        if len(parts) > 1:
            match = re.search("\\b\\d{1,2}:\\d{2} [APM]{2}\\b", parts[0])
            start_time = match.group() if match else None
            match = re.search("\\b\\d{1,2}:\\d{2} [APM]{2}\\b", parts[1])
            end_time_text = match.group() if match else None
            date = original_datetime_str.split("T")[0]
            # Format the result as ISO 8601

            input_format = "%I:%M %p %Y-%m-%d"

            # Convert the input string to a datetime object
            datetime_obj = datetime.strptime(start_time + " " + date, input_format)

            # Convert the datetime object to the desired format
            start_date_time = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
            datetime_obj = datetime.strptime(end_time_text + " " + date, input_format)

            # Convert the datetime object to the desired format
            end_date_time = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
            return (start_date_time, end_date_time, "")
        else:
            start_date_time = original_datetime_str.split("T")[0] + "T00:00:00"
            return (start_date_time, None, "Please confirm time on links")

    # Test example

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
        }

        # First check the title for each keyword
        for keyword, classification in classifications.items():
            if keyword in title or keyword in description_text:
                return classification

        return "BOARD"

    async def parse_links(item):
        anchors = await item.query_selector_all(".related-content a")
        links = []
        for anchor in anchors:
            href = await anchor.get_attribute("href") or ""
            title = await anchor.text_content() or ""
            title = re.sub("\\s+", " ", title).strip()
            if "agenda" in title.lower():
                title = "Agenda"
            elif "minute" in title.lower():
                title = "Minutes"

            links.append({"url": href, "title": title})
        return links

    page: Page = sdk.page
    try:
        await page.wait_for_selector("h1[itemprop='name']")
    except TimeoutError:
        await page.wait_for_selector(".title a")
        meeting_link = await page.query_selector(".title a")
        if meeting_link:
            link = await meeting_link.get_attribute("href")
            await page.goto(link)
            await page.wait_for_selector("h1[itemprop='name']")
        else:
            raise Exception("unexpected page!")
    title_element = await page.query_selector("h1[itemprop='name']")
    title = await title_element.inner_text()
    date_atrribute_element = await page.query_selector("[itemprop='startDate']")
    date_attribute_text = await date_atrribute_element.get_attribute("content")
    date_element = await page.query_selector("[itemprop='startDate'] p")
    date_text = await date_element.inner_text()

    start_time, end_time, time_note = await extract_and_format_date(
        date_attribute_text, date_text.strip()
    )
    description_element = await page.query_selector("div.moudle .content")
    description_text = (
        await description_element.inner_text() if description_element else ""
    )
    location_address_element = await page.query_selector("[itemprop='address']")
    location = (
        await location_address_element.inner_text()
        if location_address_element
        else None
    )
    if location:
        if "microsoft" in location.lower():
            location = {"name": "Virtual", "address": "Microsoft Teams"}
        elif "zoom" in location.lower():
            location = {"name": "Virtual", "address": "Zoom"}
        else:
            location = {"name": "", "address": location}

    if "cancel" in title.lower() or "no meeting" in title.lower():
        is_cancelled = True
    else:
        is_cancelled = False

    meeting = {
        "title": title,
        "description": description_text,  # noqa: E501
        "classification": await parse_classification(title, description_text),
        "start_time": await change_timezone(start_time) if start_time else None,
        "end_time": await change_timezone(end_time) if end_time else None,
        "time_notes": time_note,
        "is_all_day_event": False,
        "location": location,
        "links": await parse_links(page),
    }
    meeting["is_cancelled"] = is_cancelled
    await sdk.save_data(meeting)


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            (
                "https://cuyahogacounty.gov/boards-and-commissions/"
                "bc-event-detail/2024/11/26/ccesab-calendar/"
                "11-26-24--ccesab-law-enforcement-subcommittee"
            ),
            headless=False,
            harness=playwright_harness,
            schema={
                "links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL link to the document or resource related to the meeting.",  # noqa: E501
                            },
                            "title": {
                                "type": "string",
                                "description": "The title or label for the link, providing context for what the document or resource is.",  # noqa: E501
                            },
                        },
                        "description": "List of dictionaries with title and href for relevant links (eg. agenda, minutes). Empty list if no relevant links are available.",  # noqa: E501
                    },
                    "description": "A list of links related to the meeting, such as references to meeting agendas, minutes, or other documents.",  # noqa: E501
                },
                "title": {
                    "type": "string",
                    "description": "Title of the meeting (e.g., 'Regular council meeting').",  # noqa: E501
                },
                "end_time": {
                    "type": "datetime",
                    "description": "The scheduled end time of the meeting. Often unavailable.",  # noqa: E501
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the venue where the meeting will take place.",  # noqa: E501
                        },
                        "address": {
                            "type": "string",
                            "description": "The full address of the meeting venue. Sometimes, it will include an online meeting link if the physical location is not provided. ",  # noqa: E501
                        },
                    },
                    "description": "Details about the meeting's location, including the name and address of the venue.",  # noqa: E501
                },
                "start_time": {
                    "type": "datetime",
                    "description": "The scheduled start time of the meeting.",  # noqa: E501
                },
                "time_notes": {
                    "type": "string",
                    "description": "If needed, a note about the meeting time. Empty string otherwise. Typically empty string.",  # noqa: E501
                },
                "description": {  # noqa: E501
                    "type": "string",
                    "description": "Specific meeting description; empty string if unavailable.",  # noqa: E501
                },
                "is_cancelled": {
                    "type": "boolean",
                    "description": "If there are any fields in the site that shows that the meeting has been cancelled True.",  # noqa: E501
                },
                "classification": {
                    "type": "string",
                    "expression": "UPPER(classification)",
                    "description": "The classification of the meeting, such as 'Regular Business Meeting', 'Norcross Development Authority', 'City Council Work Session' etc.",  # noqa: E501
                },
                "is_all_day_event": {
                    "type": "boolean",
                    "description": "Boolean for all-day events. Typically False.",  # noqa: E501
                },
            },
        )
    )
