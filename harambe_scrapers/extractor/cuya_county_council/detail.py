import asyncio
from typing import Any

from harambe import SDK
from harambe import PlaywrightUtils as Pu
from harambe.contrib import soup_harness
from playwright.async_api import Page


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    page: Page = sdk.page
    # await page.wait_for_selector(".related-content a")
    all_links = await page.query_selector_all(".related-content a")
    links = []
    for lnk in all_links:
        href = await lnk.get_attribute("href")
        link_name = await lnk.inner_text()
        links.append({"title": link_name, "url": href})

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
            "council": "CITY_COUNCIL",
        }
        # First check the title for each keyword
        for keyword, classification in classifications.items():
            if keyword in title or keyword in description_text:
                return classification
        return None

    location = await Pu.get_text(
        page, 'p[itemprop="address"]'
    )  # Closest match to council
    # Not included in the data
    meeting = {
        "title": context["title"],
        "description": context["description"],  # noqa: E501
        "classification": await parse_classification(
            context["title"], context["description"]
        ),
        "start_time": context["start_time"],
        "end_time": None,
        "is_all_day_event": context["is_all_day_event"],
        "time_notes": None,
        "location": {"address": location, "name": None} if location else None,
        "links": links,
        "is_cancelled": True if "cancelled" in context["title"].lower() else False,
    }
    await sdk.save_data(meeting)


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            (
                "https://cuyahogacounty.gov/council/council-event-details/"
                "2024/01/09/council/committee-of-the-whole-meeting---01-09-2024"
            ),
            headless=False,
            harness=soup_harness,
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
