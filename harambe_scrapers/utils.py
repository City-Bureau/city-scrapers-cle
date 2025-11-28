"""
Common utilities for harambe scrapers.
Shared functions for OCD Event format transformation and ID generation.
"""

import hashlib
import re
from datetime import datetime

import pytz


def slugify(text):
    """Convert text to URL slug format"""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "_", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def generate_id(name, start_time, scraper_name):
    """Generate cityscrapers.org/id format."""
    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    date_str = dt.strftime("%Y%m%d%H%M")
    name_slug = slugify(name)
    return f"{scraper_name}/{date_str}/x/{name_slug}"


def generate_ocd_id(scraper_id):
    """Generate OCD event ID using MD5 hash"""
    hash_obj = hashlib.md5(scraper_id.encode())
    hash_hex = hash_obj.hexdigest()
    return (
        f"ocd-event/{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-"
        f"{hash_hex[16:20]}-{hash_hex[20:32]}"
    )


def determine_status(is_cancelled, start_time):
    """Determine meeting status based on cancellation and time"""
    if is_cancelled:
        return "canceled"

    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    now = datetime.now(dt.tzinfo)

    if dt > now:
        return "tentative"
    else:
        return "passed"


def create_ocd_event(
    title,
    start_time,
    scraper_name,
    agency_name,
    timezone,
    description="",
    classification=None,
    location=None,
    links=None,
    end_time=None,
    is_cancelled=False,
    source_url="",
    all_day=False,
):
    """
    Create a standardized OCD Event format dictionary.

    Args:
        title: Event title
        start_time: ISO format datetime string
        scraper_name: Name of the scraper (e.g., "cle_planning_commission")
        agency_name: Name of the agency hosting the event
        timezone: Timezone string (e.g., "America/Detroit")
        description: Event description (optional)
        classification: Event classification (optional, default "COMMITTEE")
        location: Location dict with 'name' and 'address' keys (optional)
        links: List of link dicts with 'url' and 'title' keys (optional)
        end_time: ISO format datetime string (optional)
        is_cancelled: Boolean indicating if event is cancelled (optional)
        source_url: URL where the event was found (optional)

    Returns:
        Dictionary in OCD Event format
    """
    # Generate IDs
    scraper_id = generate_id(title, start_time, scraper_name)
    ocd_id = generate_ocd_id(scraper_id)

    # Determine status
    status = determine_status(is_cancelled, start_time)

    if location is None:
        location = {"name": "", "address": ""}

    if links is None:
        links = []

    tz = pytz.timezone(timezone)
    updated_at = tz.localize(datetime.now()).isoformat(timespec="seconds")

    return {
        "_type": "event",
        "_id": ocd_id,
        "updated_at": updated_at,
        "name": title,
        "description": description,
        "classification": classification,
        "status": status,
        "all_day": all_day,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": timezone,
        "location": {
            "url": "",
            "name": location.get("name", ""),
            "coordinates": None,
        },
        "documents": [],
        "links": links,
        "sources": [{"url": source_url, "note": ""}],
        "participants": [
            {
                "note": "host",
                "name": agency_name,
                "entity_type": "organization",
                "entity_name": agency_name,
                "entity_id": "",
            }
        ],
        "extras": {
            "cityscrapers.org/id": scraper_id,
            "cityscrapers.org/agency": agency_name,
            "cityscrapers.org/time_notes": "",
            "cityscrapers.org/address": location.get("address", ""),
        },
    }
