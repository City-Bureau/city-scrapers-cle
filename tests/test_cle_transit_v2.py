"""
Unit tests for Greater Cleveland Regional Transit Authority v2 scraper.
"""

from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from harambe_scrapers.cle_transit import DetailSDK, ListingSDK
from harambe_scrapers.extractor.cle_transit.detail import scrape as detail_scrape
from harambe_scrapers.extractor.cle_transit.listing import scrape as listing_scrape


@pytest.fixture
def fixture_html():
    parent_dir = Path(__file__).parent
    fixture_path = parent_dir / "files" / "cle_transit.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.fixture
def fixture_detail_html():
    parent_dir = Path(__file__).parent
    fixture_path = parent_dir / "files" / "cle_transit_meeting.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.mark.asyncio
async def test_listing_scraper_extracts_event_urls_from_html(fixture_html):
    """Test that listing scraper correctly extracts event URLs from HTML"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_html)

        event_urls = []
        event_contexts = {}
        sdk = ListingSDK(page, event_urls, event_contexts)

        # Mock page.goto to prevent navigation since we've already loaded the fixture
        original_goto = page.goto

        async def mock_goto(url):
            # Don't navigate, fixture is already loaded
            pass
        page.goto = mock_goto

        # Call the actual listing scraper function
        await listing_scrape(sdk, "https://www.riderta.com/about", {})

        # Restore original goto
        page.goto = original_goto

        assert len(event_urls) > 0

        expected_urls = [
            "/events/2024-1-23/board-meeting",
            "/events/2024/1/26/board-retreat",
            "/events/2024-2-27/committee-and-board-meetings",
            "/events/2024-3-5/committee-and-board-meetings",
        ]

        for expected_url in expected_urls:
            assert expected_url in event_urls

        first_url = event_urls[0]
        assert first_url in event_contexts
        assert "date" in event_contexts[first_url]

        await browser.close()


@pytest.mark.asyncio
async def test_detail_scraper_extracts_meeting_data_from_html(fixture_detail_html):
    """Test detail scraper extracts title, time, location, and links from HTML"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_detail_html)

        sdk = DetailSDK(page)
        await detail_scrape(
            sdk,
            "https://www.riderta.com/events/2024-7-30/board-meeting",
            {"date": "Jul 30, 2024"},
        )

        assert sdk.data is not None

        assert sdk.data["title"] == "Board Meeting"
        assert "2024-07-30" in sdk.data["start_time"]
        assert "09:00" in sdk.data["start_time"]
        assert "11:00" in sdk.data["end_time"]

        location = sdk.data["location"]
        assert location is not None
        assert "1240 West 6th" in location["address"]
        assert "Cleveland" in location["address"]

        links = sdk.data["links"]
        assert len(links) == 3
        assert any(
            "Board%26CmtPackage.pdf" in link["url"] for link in links
        )
        assert any("Presentations.pdf" in link["url"] for link in links)
        assert any(
            "CompensationMinutes.pdf" in link["url"] for link in links
        )

        assert sdk.data["classification"] == "BOARD"
        assert sdk.data["is_cancelled"] is False

        await browser.close()
