"""Archive Harambe scraper URLs to Wayback Machine."""

import asyncio
import json
import os
import random
from urllib.parse import quote, unquote, urlparse

import aiohttp
from azure.storage.blob import BlobServiceClient

CITY = "cle"
CONTAINER = f"meetings-feed-{CITY}"
WAYBACK_URL = "https://web.archive.org/save/"
MAX_LINKS = 3
MAX_CONCURRENT = 2
REQUEST_DELAY = 4
TIMEOUT = 10

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
    """Check if URL is valid (has http(s) scheme and proper domain)."""
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and "." in parsed.netloc
    except Exception:
        return False


def get_urls_to_archive(meeting):
    """Extract URLs to archive."""
    urls = []

    sources = meeting.get("sources", [])
    if sources:
        source_url = sources[0].get("url", "")
        if "legistar" in source_url and "Calendar.aspx" not in source_url:
            urls.append(source_url)

    link_urls = [
        link.get("url")
        for link in meeting.get("links", [])
        if is_valid_url(link.get("url"))
    ]
    if len(link_urls) > MAX_LINKS:
        link_urls = random.sample(link_urls, MAX_LINKS)
    urls.extend(link_urls)

    return urls


async def archive_url(session, url, index, total):
    """Send archive request to Wayback Machine."""
    encoded_url = quote(url, safe=":/?&=#")
    try:
        async with session.get(
            WAYBACK_URL + encoded_url,
            headers={"User-Agent": "City Scrapers Harambe Archive Bot"},
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
        ) as response:
            if response.status in (200, 302):
                archived = response.headers.get("Content-Location", str(response.url))
                print(f"[{index}/{total}] ✓ {archived}", flush=True)
                return ("success", url)
            elif response.status == 429:
                print(f"[{index}/{total}] ⏳ Rate limited: {url}", flush=True)
                return ("rate_limited", url)
            else:
                print(f"[{index}/{total}] ✗ ({response.status}) {url}", flush=True)
                return ("failed", url)
    except asyncio.TimeoutError:
        print(f"[{index}/{total}] → Sent (timeout ok): {url}", flush=True)
        return ("success", url)
    except Exception as e:
        print(f"[{index}/{total}] ✗ Error: {e}", flush=True)
        return ("failed", url)


async def archive_batch(urls):
    """Send all archive requests with rate limiting."""
    total = len(urls)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def bounded_archive(url, index):
        async with semaphore:
            return await archive_url(session, url, index, total)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, url in enumerate(urls, 1):
            task = asyncio.create_task(bounded_archive(url, i))
            tasks.append(task)
            await asyncio.sleep(REQUEST_DELAY)

        results = await asyncio.gather(*tasks, return_exceptions=True)

    success_urls = [r[1] for r in results if isinstance(r, tuple) and r[0] == "success"]
    rate_limited_urls = [
        r[1] for r in results if isinstance(r, tuple) and r[0] == "rate_limited"
    ]
    failed_urls = [r[1] for r in results if isinstance(r, tuple) and r[0] == "failed"]

    return success_urls, rate_limited_urls, failed_urls


def main():
    print(f"Harambe Archive - {CITY.upper()}", flush=True)

    meetings = download_latest_json()
    print(f"Downloaded {len(meetings)} meetings", flush=True)

    harambe_meetings = filter_harambe_meetings(meetings)
    print(f"Found {len(harambe_meetings)} Harambe meetings", flush=True)

    all_urls = []
    for meeting in harambe_meetings:
        all_urls.extend(get_urls_to_archive(meeting))

    all_urls = list(set(unquote(url) for url in all_urls))
    print(f"Found {len(all_urls)} unique URLs to archive", flush=True)

    if not all_urls:
        print("No URLs to archive. Done.", flush=True)
        return

    success_urls, rate_limited_urls, failed_urls = asyncio.run(archive_batch(all_urls))

    print(
        f"\nDone: {len(success_urls)} sent, "
        f"{len(rate_limited_urls)} rate-limited, {len(failed_urls)} failed",
        flush=True,
    )

    if rate_limited_urls:
        print("\nRate-limited URLs:", flush=True)
        for url in rate_limited_urls:
            print(f"  - {url}", flush=True)

    if failed_urls:
        print("\nFailed URLs:", flush=True)
        for url in failed_urls:
            print(f"  - {url}", flush=True)


if __name__ == "__main__":
    main()
