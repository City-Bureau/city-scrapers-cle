"""
Cuyahoga County Emergency Services Advisory Board - Production Scraper
Orchestrates category->listing->detail scrapers with Azure upload support.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

from harambe_scrapers.extractor.cuya_emergency_services_advisory.category import (
    scrape as category_scrape,
)
from harambe_scrapers.extractor.cuya_emergency_services_advisory.detail import (
    scrape as detail_scrape,
)
from harambe_scrapers.extractor.cuya_emergency_services_advisory.listing import (
    scrape as listing_scrape,
)
from harambe_scrapers.observers import DataCollector
from harambe_scrapers.utils import create_ocd_event

OUTPUT_DIR = Path("harambe_scrapers/output")
SCRAPER_NAME = "cuya_emergency_services_advisory"
AGENCY_NAME = "Cuyahoga County Emergency Services Advisory Board"
TIMEZONE = "America/Detroit"
START_URL = "https://bc.cuyahogacounty.us/en-US/CC-EmergencySrvcsAdvsryBrd.aspx"


class CategorySDK:
    def __init__(self, page, year_urls: list):
        self.page = page
        self.year_urls = year_urls

    async def enqueue(self, url: str):
        self.year_urls.append(url)

    async def save_data(self, data: dict):
        pass


class ListingSDK:
    def __init__(self, page, event_urls: list):
        self.page = page
        self.event_urls = event_urls

    async def enqueue(self, url: str):
        self.event_urls.append(url)

    async def save_data(self, data: dict):
        pass


class DetailSDK:
    def __init__(self, page):
        self.page = page
        self.data = None

    async def enqueue(self, url: str):
        pass

    async def save_data(self, data: dict):
        self.data = data


class CuyaEmergencyServicesOrchestrator:
    def __init__(self, headless: bool = True, max_items: Optional[int] = None):
        self.headless = headless
        self.max_items = max_items
        self.year_urls = []
        self.event_urls = []
        self.observer = DataCollector(SCRAPER_NAME, TIMEZONE)
        self.current_url = None

    async def run_category_stage(self, page):
        print("\n" + "=" * 60)
        print("[Stage 1/3] Category Stage - Generating year URLs")
        print("=" * 60)

        category_sdk = CategorySDK(page, self.year_urls)
        await category_scrape(category_sdk, START_URL, {})

        print(f"\nGenerated {len(self.year_urls)} year URLs")
        if self.year_urls:
            print(f"Sample URL: {self.year_urls[0]}")
        return self.year_urls

    async def run_listing_stage(self, page):
        print("\n" + "=" * 60)
        print("[Stage 2/3] Listing Stage - Extracting event URLs")
        print("=" * 60)

        # Convert relative URLs to absolute URLs
        base_url = (
            "https://cuyahogacounty.gov/boards-and-commissions/" "board-details/other"
        )
        absolute_year_urls = []
        for year_url in self.year_urls:
            if year_url.startswith("http"):
                absolute_year_urls.append(year_url)
            else:
                absolute_year_urls.append(f"{base_url}/{year_url.lstrip('/')}")
        self.year_urls = absolute_year_urls

        total_years = len(self.year_urls)
        print(f"\nProcessing {total_years} year pages...")

        for i, year_url in enumerate(self.year_urls, 1):
            try:
                await page.goto(year_url, wait_until="domcontentloaded", timeout=30000)
                listing_sdk = ListingSDK(page, self.event_urls)
                await listing_scrape(listing_sdk, year_url, {})
                print(f"  [{i}/{total_years}] {year_url}")
            except Exception as e:
                print(f"  [{i}/{total_years}] ✗ Error: {e}")
                continue

        self.event_urls = list(set(self.event_urls))
        print(f"\nFound {len(self.event_urls)} unique event URLs")
        return self.event_urls

    async def run_detail_stage(self, page, event_url: str) -> Optional[dict]:
        try:
            # Convert relative URL to absolute URL
            if event_url.startswith("http"):
                absolute_url = event_url
            else:
                absolute_url = f"https://cuyahogacounty.gov{event_url}"

            self.current_url = absolute_url
            await page.goto(absolute_url, wait_until="domcontentloaded", timeout=30000)
            detail_sdk = DetailSDK(page)
            await detail_scrape(detail_sdk, absolute_url, {})
            return detail_sdk.data
        except Exception as e:
            print(f"    ✗ Error extracting {event_url}: {e}")
            return None

    def transform_to_ocd_format(self, raw_data: dict) -> dict:
        all_day = raw_data.get("is_all_day_event")
        if all_day is None:
            all_day = False

        location = raw_data.get("location") or {}

        return create_ocd_event(
            title=raw_data.get("title") or "Emergency Services Advisory Board Meeting",
            start_time=raw_data["start_time"],
            scraper_name=SCRAPER_NAME,
            agency_name=AGENCY_NAME,
            timezone=TIMEZONE,
            description=raw_data.get("description") or "",
            classification=raw_data.get("classification"),
            location=location,
            links=raw_data.get("links") or [],
            end_time=raw_data.get("end_time"),
            is_cancelled=raw_data.get("is_cancelled", False),
            source_url=self.current_url,
            all_day=all_day,
        )

    async def run(self):
        print("=" * 70)
        print(AGENCY_NAME)
        print("=" * 70)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await self.run_category_stage(page)

                await self.run_listing_stage(page)

                print("\n" + "=" * 60)
                print("[Stage 3/3] Detail Stage - Extracting meeting data")
                print("=" * 60)

                total_events = len(self.event_urls)
                if self.max_items:
                    self.event_urls = self.event_urls[: self.max_items]
                    total_events = len(self.event_urls)
                    print(
                        f"\nProcessing {total_events} events "
                        f"(limited to {self.max_items})..."
                    )
                else:
                    print(f"\nProcessing {total_events} events...")

                for i, event_url in enumerate(self.event_urls, 1):
                    print(f"\n[{i}/{total_events}] {event_url}")

                    raw_data = await self.run_detail_stage(page, event_url)

                    if raw_data and raw_data.get("start_time"):
                        ocd_event = self.transform_to_ocd_format(raw_data)
                        await self.observer.on_save_data(ocd_event)
                        print(f"  ✓ Saved: {ocd_event['name']}")
                    else:
                        print("  ✗ Skipped (missing start_time)")

                print("\n" + "=" * 70)
                print(f"Scraping Complete: {len(self.observer.data)} meetings")
                print("=" * 70)

                if self.observer.data:
                    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = OUTPUT_DIR / f"{SCRAPER_NAME}_{timestamp}.json"

                    with open(output_file, "w", encoding="utf-8") as f:
                        for meeting in self.observer.data:
                            if "__url" in meeting:
                                del meeting["__url"]
                            f.write(json.dumps(meeting, ensure_ascii=False) + "\n")

                    print(f"\n✓ Data saved to: {output_file}")

                    if self.observer.azure_client:
                        print("✓ Data uploaded to Azure Blob Storage")
                    else:
                        print(
                            "ℹ Azure upload not configured "
                            "(set AZURE_* environment variables)"
                        )

            finally:
                await browser.close()


async def main():
    orchestrator = CuyaEmergencyServicesOrchestrator(headless=True, max_items=None)
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
