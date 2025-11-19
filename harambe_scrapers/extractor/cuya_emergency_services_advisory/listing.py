import asyncio
from typing import Any

from harambe import SDK
from harambe.contrib import playwright_harness
from playwright.async_api import Page


# https://github.com/City-Bureau/city-scrapers-cle/blob/main/city_scrapers/spiders/cuya_emergency_services_advisory.py
async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    async def fetch_links(page):
        await page.wait_for_selector(".bceventgrid td > a")
        all_link_elements = await page.query_selector_all(".bceventgrid td > a")
        for link_element in all_link_elements:
            await sdk.enqueue(await link_element.get_attribute("href"))

    page: Page = sdk.page
    await fetch_links(page)


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            (
                "https://cuyahogacounty.gov/boards-and-commissions/"
                "board-details/other/emergency-services-advisory-board"
                "?year=2025"
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
