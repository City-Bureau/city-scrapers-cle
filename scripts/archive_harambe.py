"""Archive Harambe scraper URLs to Wayback Machine."""

import asyncio
import json
import os
import random
from urllib.parse import unquote

import aiohttp
from azure.storage.blob import BlobServiceClient

CITY = "cle"
CONTAINER = f"meetings-feed-{CITY}"
WAYBACK_URL = "https://web.archive.org/save/"
MAX_LINKS = 3
MAX_CONCURRENT = 3  # Match Scrapy's concurrency

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


def is_valid_url(url):
    """Check if URL is valid (starts with http:// or https://)."""
    return url and (url.startswith("http://") or url.startswith("https://"))


def get_urls_to_archive(meeting):
    """Extract URLs to archive (matching Scrapy's middleware logic)."""
    urls = []

    # 1. Add source URL only if contains "legistar" (not Calendar.aspx)
    sources = meeting.get("sources", [])
    if sources:
        source_url = sources[0].get("url", "")
        if "legistar" in source_url and "Calendar.aspx" not in source_url:
            urls.append(source_url)

    # 2. Add up to MAX_LINKS random links (only valid URLs)
    link_urls = [
        link.get("url")
        for link in meeting.get("links", [])
        if is_valid_url(link.get("url"))
    ]
    if len(link_urls) > MAX_LINKS:
        link_urls = random.sample(link_urls, MAX_LINKS)
    urls.extend(link_urls)

    return urls


class ArchiveStats:
    """Track archive statistics."""

    def __init__(self, total):
        self.total = total
        self.completed = 0
        self.success = 0
        self.failed = 0
        self.lock = asyncio.Lock()

    async def record(self, success):
        async with self.lock:
            self.completed += 1
            if success:
                self.success += 1
            else:
                self.failed += 1
            return self.completed


async def archive_url(session, url, stats, delay_event):
    """Submit URL to Wayback Machine. Returns True if successful."""
    # Wait if rate limited
    while delay_event.is_set():
        await asyncio.sleep(1)

    try:
        async with session.get(
            WAYBACK_URL + url,
            headers={"User-Agent": "City Scrapers Harambe Archive Bot"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            num = await stats.record(response.status == 200)

            if response.status == 200:
                archived = response.headers.get("Content-Location", str(response.url))
                print(f"[{num}/{stats.total}] ✓ {archived}", flush=True)
                return True
            elif response.status == 429:
                print(
                    f"[{num}/{stats.total}] ⏳ Rate limited, waiting 60s...", flush=True
                )
                delay_event.set()
                await asyncio.sleep(60)
                delay_event.clear()
                # Retry once
                return await archive_url_retry(session, url, stats)
            else:
                print(
                    f"[{num}/{stats.total}] ✗ ({response.status}) {url[:60]}",
                    flush=True,
                )
                return False
    except asyncio.TimeoutError:
        num = await stats.record(False)
        print(f"[{num}/{stats.total}] ✗ Timeout: {url[:60]}", flush=True)
        return False
    except Exception as e:
        num = await stats.record(False)
        print(f"[{num}/{stats.total}] ✗ Error: {e}", flush=True)
        return False


async def archive_url_retry(session, url, stats):
    """Single retry for rate-limited requests."""
    try:
        async with session.get(
            WAYBACK_URL + url,
            headers={"User-Agent": "City Scrapers Harambe Archive Bot"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status == 200:
                archived = response.headers.get("Content-Location", str(response.url))
                print(f"  ↳ Retry ✓ {archived}", flush=True)
                return True
            else:
                print(f"  ↳ Retry ✗ ({response.status})", flush=True)
                return False
    except Exception:
        return False


async def archive_batch(urls):
    """Archive URLs concurrently with rate limit handling."""
    stats = ArchiveStats(len(urls))
    delay_event = asyncio.Event()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def bounded_archive(url):
        async with semaphore:
            return await archive_url(session, url, stats, delay_event)

    async with aiohttp.ClientSession() as session:
        tasks = [bounded_archive(url) for url in urls]
        await asyncio.gather(*tasks)

    return stats


def main():
    print(f"Harambe Archive - {CITY.upper()}", flush=True)

    meetings = download_latest_json()
    print(f"Downloaded {len(meetings)} meetings", flush=True)

    harambe_meetings = filter_harambe_meetings(meetings)
    print(f"Found {len(harambe_meetings)} Harambe meetings", flush=True)

    # Collect all URLs
    all_urls = []
    for meeting in harambe_meetings:
        all_urls.extend(get_urls_to_archive(meeting))

    # Deduplicate (unquote to normalize encoding differences like space vs %20)
    all_urls = list(set(unquote(url) for url in all_urls))

    print(f"Found {len(all_urls)} unique URLs to archive", flush=True)

    if not all_urls:
        print("No URLs to archive. Done.", flush=True)
        return

    # Run async archive
    stats = asyncio.run(archive_batch(all_urls))

    print(f"\nDone: {stats.success}/{stats.total} URLs archived", flush=True)


if __name__ == "__main__":
    main()
