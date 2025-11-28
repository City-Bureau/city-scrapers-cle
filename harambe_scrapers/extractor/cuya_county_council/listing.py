import asyncio
from typing import Any

import requests
from harambe import SDK
from harambe.contrib import soup_harness


async def scrape(
    sdk: SDK, current_url: str, context: dict[str, Any], *args: Any, **kwargs: Any
) -> None:
    from datetime import date, datetime

    import pytz

    timezone = "America/Detroit"

    headers = {"Content-Type": "application/json"}

    async def parse_date(date_str):
        """
        Convert millisecond Unix timestamp "/Date(1714399200000)/"
        to naive datetime.
        """
        clean_date_str = date_str.replace("/Date(", "").replace(")/", "")
        try:
            timestamp = int(int(clean_date_str) / 1000)
            date = datetime.fromtimestamp(timestamp, pytz.utc)
            local_date = date.astimezone(pytz.timezone(timezone))
            return local_date.replace(tzinfo=None)
        except ValueError:
            print(f"Error parsing date: {date_str}")
            return None

    def convert_datetime_format(input_datetime_str, target_timezone=timezone):
        # Parse the input datetime string
        naive_datetime = datetime.strptime(str(input_datetime_str), "%Y-%m-%d %H:%M:%S")

        # Define the target timezone
        target_tz = pytz.timezone(target_timezone)

        # Localize the naive datetime to the target timezone
        localized_datetime = target_tz.localize(naive_datetime)

        # Format the datetime in the desired ISO 8601 format with timezone offset
        formatted_datetime = localized_datetime.isoformat()

        return formatted_datetime

    # Generate the start URL

    async def generate_start_url():
        current_year = datetime.now().year

        # Calculate the range
        start_date = date(current_year - 1, 1, 1)
        end_date = date(current_year + 1, 12, 31)
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        return (
            f"https://www.cuyahogacounty.gov/web-interface/events?"
            f"StartDate={start_date_str}&EndDate={end_date_str}"
            f"&EventSchedulerViewMode=month&UICulture="
            f"&Id=175b0fba-07f2-4b3e-a794-e499e98c0a93"
            f"&CurrentPageId=b38b8f62-8073-4d89-9027-e7a13e53248e"
            f"&sf_site=f3ea71cd-b8c9-4a53-b0db-ee5d552472fc"
        )

    url = await generate_start_url()
    response = requests.get(url, headers=headers)

    data = response.json()
    for item in data:
        start = await parse_date(item.get("Start", None))

        start_date_ = convert_datetime_format(start)
        event_url = (
            "https://cuyahogacounty.gov/council/council-event-details"
            + item["EventUrl"]
        )
        await sdk.enqueue(
            event_url,
            context={
                "title": item.get("Title", ""),
                "description": item.get("Description", ""),  # noqa: E501
                "start_time": start_date_,
                "is_all_day_event": item.get("IsAllDay", None),
            },
        )


if __name__ == "__main__":
    asyncio.run(
        SDK.run(
            scrape,
            "http://council.cuyahogacounty.us/en-US/about-council.aspx",
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
