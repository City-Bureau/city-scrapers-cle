"""Archive Harambe scraper URLs to Wayback Machine."""

import json
import os
import random
import time

import requests
from azure.storage.blob import BlobServiceClient

CITY = "cle"
CONTAINER = f"meetings-feed-{CITY}"
WAYBACK_URL = "https://web.archive.org/save/"
MAX_LINKS = 3

HARAMBE_SCRAPERS = [
    "cle_building_standards",
    "cle_planning_commission",
    "cle_transit",
    "cuya_arts_culture",
    "cuya_county_council",
    "cuya_emergency_services_advisory",
]


def download_latest_json(container=CONTAINER):
    """Download latest.json from Azure."""
    account_name = os.getenv("AZURE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_ACCOUNT_KEY")

    if not account_name or not account_key:
        raise ValueError("AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY required")

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_container_client(container).get_blob_client(
        "latest.json"
    )

    content = blob_client.download_blob().readall().decode("utf-8")
    return [json.loads(line) for line in content.strip().split("\n") if line]


def filter_harambe_meetings(meetings, scrapers=HARAMBE_SCRAPERS):
    """Filter to only Harambe scraper meetings."""
    return [
        m
        for m in meetings
        if any(
            s in m.get("extras", {}).get("cityscrapers.org/id", "") for s in scrapers
        )
    ]


def get_urls_to_archive(meeting, max_links=MAX_LINKS):
    """Extract URLs to archive following Scrapy's logic."""
    urls = []

    # Source URL only if contains "legistar" (not Calendar.aspx)
    sources = meeting.get("sources", [])
    if sources:
        source_url = sources[0].get("url", "")
        if "legistar" in source_url and "Calendar.aspx" not in source_url:
            urls.append(source_url)

    # Random sample of links and documents (max 3 each)
    for field in ["links", "documents"]:
        items = meeting.get(field, [])
        item_urls = [item.get("url") for item in items if item.get("url")]
        if len(item_urls) > max_links:
            item_urls = random.sample(item_urls, max_links)
        urls.extend(item_urls)

    return urls


def archive_url(url, _retry=False):
    """Submit URL to Wayback Machine. Returns True if successful."""
    try:
        response = requests.get(
            WAYBACK_URL + url,
            headers={"User-Agent": "City Scrapers Harambe Archive Bot"},
            timeout=30,
        )
        if response.status_code == 200:
            # Get archived URL from Content-Location header or final URL
            archived = response.headers.get("Content-Location", response.url)
            print(f"✓ {archived}")
            return True
        elif response.status_code == 429 and not _retry:
            print("⏳ Rate limited, waiting 60s...")
            time.sleep(60)
            return archive_url(url, _retry=True)
        else:
            print(f"✗ ({response.status_code}) {url[:60]}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print(f"Harambe Archive - {CITY.upper()}")

    meetings = download_latest_json()
    print(f"Downloaded {len(meetings)} meetings")

    harambe_meetings = filter_harambe_meetings(meetings)
    print(f"Found {len(harambe_meetings)} Harambe meetings")

    # Collect all URLs to show progress
    all_urls = []
    for meeting in harambe_meetings:
        all_urls.extend(get_urls_to_archive(meeting))

    total_urls = len(all_urls)
    print(f"Found {total_urls} URLs to archive")

    if total_urls == 0:
        print("No URLs to archive. Done.")
        return

    archived = 0
    for i, url in enumerate(all_urls, 1):
        print(f"[{i}/{total_urls}] ", end="", flush=True)
        if archive_url(url):
            archived += 1
        time.sleep(1.5)

    print(f"\nDone: {archived}/{total_urls} URLs archived")


if __name__ == "__main__":
    main()
