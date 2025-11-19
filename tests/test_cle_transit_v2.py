"""
Unit tests for Greater Cleveland Regional Transit Authority v2 scraper.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytz
from playwright.async_api import async_playwright

from harambe_scrapers.cle_transit import (
    AGENCY_NAME,
    TIMEZONE,
    DetailSDK,
    GCRTAOrchestrator,
    ListingSDK,
)
from harambe_scrapers.extractor.cle_transit.detail import (
    scrape as detail_scrape,
)
from harambe_scrapers.extractor.cle_transit.listing import scrape as listing_scrape


def get_future_datetime(days_ahead=30):
    tz = pytz.timezone(TIMEZONE)
    return (datetime.now(tz) + timedelta(days=days_ahead)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )


def test_transform_to_ocd_format():
    orchestrator = GCRTAOrchestrator(headless=True)
    orchestrator.current_url = (
        "https://www.riderta.com/events/2024-1-23/board-meeting"
    )

    future_time = get_future_datetime(days_ahead=60).isoformat()
    end_time = (
        get_future_datetime(days_ahead=60) + timedelta(hours=2)
    ).isoformat()

    raw_data = {
        "title": "Community Advisory Committee Meeting",
        "start_time": future_time,
        "end_time": end_time,
        "description": "Regular committee meeting",
        "classification": "COMMITTEE",
        "location": {
            "name": "RTA Headquarters",
            "address": "1240 West 6th Street",
        },
        "links": [{"url": "agenda.pdf", "title": "Agenda"}],
        "is_cancelled": False,
        "is_all_day_event": False,
    }

    result = orchestrator.transform_to_ocd_format(raw_data)

    assert result["name"] == "Community Advisory Committee Meeting"
    assert result["classification"] == "COMMITTEE"
    assert result["status"] == "tentative"
    assert result["all_day"] is False
    assert result["extras"]["cityscrapers.org/agency"] == AGENCY_NAME


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
async def test_listing_scrape_with_real_html(fixture_html):
    """Integration test with real HTML fixture"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_html)

        event_urls = []
        event_contexts = {}
        sdk = ListingSDK(page, event_urls, event_contexts)

        original_goto = page.goto
        page.goto = AsyncMock()

        await listing_scrape(sdk, "http://www.riderta.com/about", {})

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
async def test_detail_scrape_with_real_html(fixture_detail_html):
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
