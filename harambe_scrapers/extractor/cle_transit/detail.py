import asyncio
import datetime
import re
from typing import Any

from harambe import SDK
from harambe.contrib import playwright_harness
from playwright.async_api import Page, TimeoutError


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    page: Page = sdk.page
    import pytz
    from dateparser import parse

    async def change_timezone(date):
        timezone = "America/Detroit"

        # Convert string to naive datetime object
        naive_datetime = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

        # Get the timezone object
        tz = pytz.timezone(timezone)

        # Add timezone to the naive datetime
        localized_datetime = tz.localize(naive_datetime)

        # Format the localized datetime as ISO 8601 string
        iso_format = localized_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")
        # Adjusting the offset format to include a colon
        iso_format_with_colon = iso_format[:-2] + ":" + iso_format[-2:]
        return iso_format_with_colon

    async def _parse_location():
        """Parse or generate location."""
        location_selectors = [
            "views-field-field-event-location-address-line1",
            "views-field-field-event-location-address-line2",
            "views-field-field-event-location-locality",
            "views-field-field-event-location-administrative-area",
            "views-field-field-event-location-postal-code",
        ]
        address = ""
        for selector in location_selectors:
            address_part = await page.locator(f".{selector} strong").text_content()
            if address_part:
                if "address-line1" in selector:
                    address = address + address_part + ", "
                else:
                    address = address + address_part + " "

        # Condense whitespace
        clean_address = re.sub("\\s+", " ", address).strip()
        return {"name": "", "address": clean_address}

    async def _parse_links():
        """Parse or generate links."""
        attachment_links = await page.locator(
            ".view-event-attachments.view-id-event_attachments a"
        ).all()
        links = []
        for attachment_link in attachment_links:
            abs_url = await attachment_link.get_attribute("href")
            links.append(
                {
                    "title": await attachment_link.text_content(),
                    "url": "https://www.riderta.com" + abs_url,
                }
            )
        return links

    async def _parse_title():
        """Parse or generate meeting title."""
        return await page.locator(".content > h1.title span span").text_content()

    async def _parse_date():
        """Parse start and end times from the date string."""
        meeting_duration_str = await page.locator(
            ".block-views-blockevents-date-block-1 h2"
        ).text_content()
        if "-" not in meeting_duration_str:
            # Parse the string into datetime object
            dt = datetime.datetime.strptime(meeting_duration_str, "%a, %b %d %Y, %I%p")

            # Format into the desired output
            iso_format = dt.isoformat()
            return (iso_format, None)
        date_match_str = re.search(
            "([A-Z][a-z]{2} \\d{1,2} \\d{4})", meeting_duration_str
        ).group(0)
        time_match_str = meeting_duration_str.split(",")[2].strip()
        time_matches = re.findall("\\d{1,2}(?::\\d{2})?", time_match_str)
        merdiem_matches = re.findall("(am|pm)", time_match_str)

        if len(merdiem_matches) == 2:
            start = parse(f"{date_match_str} {time_matches[0]}{merdiem_matches[0]}")
            end = parse(f"{date_match_str} {time_matches[1]}{merdiem_matches[1]}")
            return (start.isoformat(), end.isoformat())
        elif len(merdiem_matches) == 1:
            start = parse(f"{date_match_str} {time_matches[0]}{merdiem_matches[0]}")
            end = parse(f"{date_match_str} {time_matches[1]}{merdiem_matches[0]}")
            return (start.isoformat(), end.isoformat())

    async def _parse_description():
        """Parse or generate meeting description."""
        description = await page.locator(
            ".content .field--name-body.field--type-text-with-summary p"
        ).all_text_contents()
        if description:
            full_description = " ".join(description)
            # Remove extra whitespace
            return re.sub("\\s+", " ", full_description).strip()
        return ""

    async def _parse_classification(title):
        """Parse or generate classification from title."""
        if "board" in title.lower():
            return "BOARD"
        elif "committee" in title.lower():
            return "COMMITTEE"
        return None

    try:
        await page.wait_for_selector(".content > h1.title span span")
    except TimeoutError:
        return  # not a valid meeting
    title = await _parse_title()
    start, end = await _parse_date()

    start_dt = datetime.datetime.fromisoformat(start) if start else None
    end_dt = datetime.datetime.fromisoformat(end) if end else None
    is_all_day_event = (
        True
        if start_dt and end_dt and ((end_dt - start_dt).total_seconds() >= 86400)
        else None
    )
    if "cancel" in title.lower():
        is_cancelled = True
    else:
        is_cancelled = False
    meeting = {
        "title": title,
        "description": await _parse_description(),  # noqa: E501
        "classification": await _parse_classification(title),
        "start_time": await change_timezone(start),
        "end_time": await change_timezone(end) if end else None,
        "is_all_day_event": is_all_day_event,
        "time_notes": "",
        "location": await _parse_location(),
        "links": await _parse_links(),
        "is_cancelled": is_cancelled,
    }
    # Save the meeting (or yield it, depending on your use case)
    await sdk.save_data(meeting)


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            "https://www.riderta.com/events/2025/5/14/cac-ada-subcommittee-meeting",
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
