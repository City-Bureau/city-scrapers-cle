import asyncio
from typing import Any

from harambe import SDK
from harambe.contrib import playwright_harness
from playwright.async_api import Page, TimeoutError

# https://github.com/City-Bureau/city-scrapers-cle/blob/main/city_scrapers/spiders/cle_transit.py


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    page: Page = sdk.page

    async def parse_meeting_links():
        """
        Parse meeting links and follow them.
        """
        meetings = None
        # meeting_links = await page.locator(
        #     "div.inserted-view > div.calendar-event-style > "
        #     "div.view-content > .mb-4.views-row a"
        # ).all_text_contents()
        if await page.query_selector(
            "div.calendar-event-style > div.view-content > .mb-4.views-row a"
        ):
            meetings = page.locator(
                "div.calendar-event-style > div.view-content > .mb-4.views-row "
            )

        # else:
        #     meetings = await page.locator(
        #         "div.calendar-event-style > div.view-content > .mb-4.views-row "
        #     )

        if not meetings:
            # Handle the case where no links are found
            print("No meeting links found.")
            return

        # deduped_meeting_links = list(set(meeting_links))
        link_set = set()
        meeting_elements = await meetings.element_handles()
        for m in meeting_elements:
            meeting_date_element = await m.query_selector(
                ".views-field-field-event-date"
            )
            meeting_date = (
                await meeting_date_element.inner_text()
                if meeting_date_element
                else None
            )
            # if not meeting_date:
            # continue
            meeting_link_element = await m.query_selector("a")
            meeting_link = (
                await meeting_link_element.get_attribute("href")
                if meeting_link_element
                else None
            )
            if not meeting_link or meeting_link in link_set:
                continue
            link_set.add(meeting_link)
            if meeting_date:
                await sdk.enqueue(meeting_link, context={"date": meeting_date})
            else:
                await sdk.enqueue(meeting_link)
            # meeting_date =
            # if meeting_link:  # Ensure the link is not None or empty
            # await sdk.enqueue(meeting_link)

    links = [
        "https://www.riderta.com/cac",
        "https://www.riderta.com/coc",
        "https://www.riderta.com/board",
    ]
    for link in links:
        await page.goto(link)
        try:
            await page.wait_for_selector(
                "div.calendar-event-style > div.view-content > .mb-4.views-row a"
            )
        except TimeoutError:
            pass
            # await page.wait_for_selector(
            #     "div.calendar-event-style > div.view-content > "
            #     ".mb-4.views-row a[hreflang='en']"
            # )
        await parse_meeting_links()


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            "http://www.riderta.com/about",
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
