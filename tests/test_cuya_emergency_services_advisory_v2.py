"""
Unit tests for Cuyahoga County Emergency Services Advisory Board v2.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import pytz
from playwright.async_api import async_playwright

from harambe_scrapers.cuya_emergency_services_advisory import (
    AGENCY_NAME,
    TIMEZONE,
    CuyaEmergencyServicesOrchestrator,
    DetailSDK,
    ListingSDK,
)
from harambe_scrapers.extractor.cuya_emergency_services_advisory.detail import (
    scrape as detail_scrape,
)
from harambe_scrapers.extractor.cuya_emergency_services_advisory.listing import (
    scrape as listing_scrape,
)


def get_future_datetime(days_ahead=30):
    tz = pytz.timezone(TIMEZONE)
    return (datetime.now(tz) + timedelta(days=days_ahead)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )


def test_transform_to_ocd_format():
    orchestrator = CuyaEmergencyServicesOrchestrator(headless=True)
    orchestrator.current_url = (
        "https://cuyahogacounty.gov/boards-and-commissions/"
        "bc-event-detail/2024/12/12/test"
    )

    future_time = get_future_datetime(days_ahead=60).isoformat()

    raw_data = {
        "title": "Emergency Services Advisory Board Meeting",
        "start_time": future_time,
        "classification": "ADVISORY",
    }

    result = orchestrator.transform_to_ocd_format(raw_data)

    assert result["name"] == "Emergency Services Advisory Board Meeting"
    assert result["classification"] == "ADVISORY"
    assert result["status"] == "tentative"
    assert result["extras"]["cityscrapers.org/agency"] == AGENCY_NAME


@pytest.fixture
def fixture_html():
    parent_dir = Path(__file__).parent
    fixture_path = (
        parent_dir / "files" / "cuya_emergency_services_advisory.html"
    )
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.fixture
def fixture_detail_html():
    parent_dir = Path(__file__).parent
    fixture_path = (
        parent_dir / "files" / "cuya_emergency_services_advisory_detail.html"
    )
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
        sdk = ListingSDK(page, event_urls)

        await listing_scrape(
            sdk,
            (
                "https://cuyahogacounty.gov/boards-and-commissions/"
                "board-details/other/emergency-services-advisory-board"
                "?year=2024"
            ),
            {},
        )

        assert len(event_urls) > 0

        expected_urls = [
            (
                "/boards-and-commissions/bc-event-detail//"
                "2024/12/12/ccesab-calendar/12-12-24---ccesab-main"
            ),
            (
                "/boards-and-commissions/bc-event-detail//"
                "2024/11/13/ccesab-calendar/"
                "11-13-24---fire-committee-meeting"
            ),
            (
                "/boards-and-commissions/bc-event-detail//"
                "2024/10/10/ccesab-calendar/10-10-24---ccesab-main"
            ),
        ]

        for expected_url in expected_urls:
            assert expected_url in event_urls

        await browser.close()


@pytest.mark.asyncio
async def test_orchestrator_url_conversion():
    """Test relative to absolute URL conversion"""
    orchestrator = CuyaEmergencyServicesOrchestrator(headless=True)
    orchestrator.year_urls = ["emergency-services-advisory-board?year=2024"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        with patch(
            "harambe_scrapers.cuya_emergency_services_advisory."
            "listing_scrape"
        ) as mock_listing:
            mock_listing.return_value = None

            await orchestrator.run_listing_stage(page)

            assert orchestrator.year_urls[0].startswith("https://")
            assert "emergency-services-advisory-board?year=2024" in (
                orchestrator.year_urls[0]
            )

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
            (
                "https://cuyahogacounty.gov/boards-and-commissions/"
                "bc-event-detail/2024/01/09/ccesab-calendar/"
                "01-09-24---ccesab-emergency-management-committee"
            ),
            {},
        )

        assert sdk.data is not None

        assert (
            sdk.data["title"]
            == "01/09/24 - CCESAB Emergency Management Committee"
        )
        assert "2024-01-09" in sdk.data["start_time"]
        assert "09:00" in sdk.data["start_time"]
        assert "10:00" in sdk.data["end_time"]

        location = sdk.data["location"]
        assert location is not None
        assert "4747 East 49th Street" in location["address"]
        assert "Cleveland" in location["address"]

        links = sdk.data["links"]
        assert len(links) >= 1
        assert any("agenda" in link["title"].lower() for link in links)
        assert any("010924-emagenda.pdf" in link["url"] for link in links)

        assert sdk.data["classification"] == "COMMITTEE"
        assert sdk.data["is_cancelled"] is False

        await browser.close()
