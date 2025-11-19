"""
Unit tests for Cuyahoga County Council v2 scraper.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytz
from playwright.async_api import async_playwright

from harambe_scrapers.cuya_county_council import (
    AGENCY_NAME,
    TIMEZONE,
    CuyaCountyCouncilOrchestrator,
    DetailSDK,
    ListingSDK,
)
from harambe_scrapers.extractor.cuya_county_council.detail import (
    scrape as detail_scrape,
)
from harambe_scrapers.extractor.cuya_county_council.listing import (
    scrape as listing_scrape,
)


def get_future_datetime(days_ahead=30):
    tz = pytz.timezone(TIMEZONE)
    return (datetime.now(tz) + timedelta(days=days_ahead)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )


def test_transform_to_ocd_format():
    orchestrator = CuyaCountyCouncilOrchestrator(headless=True)
    orchestrator.current_url = (
        "https://cuyahogacounty.gov/council/event-details/test-meeting"
    )

    future_time = get_future_datetime(days_ahead=60).isoformat()

    raw_data = {
        "title": "Public Works Committee Meeting",
        "start_time": future_time,
        "classification": "COMMISSION",
        "location": {
            "name": "Council Chambers",
            "address": "2079 East 9th Street",
        },
        "is_cancelled": False,
    }

    result = orchestrator.transform_to_ocd_format(raw_data)

    assert result["name"] == "Public Works Committee Meeting"
    assert result["classification"] == "COMMISSION"
    assert result["status"] == "tentative"
    assert result["extras"]["cityscrapers.org/agency"] == AGENCY_NAME


@pytest.fixture
def fixture_json():
    parent_dir = Path(__file__).parent
    fixture_path = parent_dir / "files" / "cuya_county_council.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_listing_scrape_with_json_fixture(fixture_json):
    event_urls = []
    event_contexts = {}
    sdk = ListingSDK(None, event_urls, event_contexts)

    with patch(
        "harambe_scrapers.extractor.cuya_county_council.listing.requests.get"
    ) as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = fixture_json
        mock_get.return_value = mock_response

        await listing_scrape(
            sdk, "http://council.cuyahogacounty.us/en-US/about-council.aspx", {}
        )

        assert len(event_urls) > 0
        assert len(event_urls) == len(fixture_json)

        assert any(
            "public-works-procurement-contracting-committee" in url
            for url in event_urls
        )

        first_url = event_urls[0]
        assert first_url in event_contexts
        context = event_contexts[first_url]
        assert "title" in context
        assert "start_time" in context

        for url in event_urls:
            assert url.startswith(
                "https://cuyahogacounty.gov/council/council-event-details"
            )


@pytest.mark.asyncio
async def test_detail_scrape_with_context(fixture_json):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        detail_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Meeting</title></head>
        <body>
            <div class="related-content">
                <a href="/files/agenda.pdf">Meeting Agenda</a>
                <a href="/files/minutes.pdf">Previous Minutes</a>
            </div>
            <p itemprop="address">2079 East 9th Street, Cleveland, OH</p>
        </body>
        </html>
        """
        await page.set_content(detail_html)

        first_meeting = fixture_json[0]
        test_context = {
            "title": first_meeting["Title"],
            "start_time": "2024-02-21T10:00:00-05:00",
            "description": first_meeting["Description"],
            "is_all_day_event": first_meeting["IsAllDay"],
        }

        sdk = DetailSDK(page)
        await detail_scrape(
            sdk,
            "https://cuyahogacounty.gov/council/council-event-details"
            "/2024/02/21/council/test",
            test_context,
        )

        assert sdk.data is not None
        assert (
            sdk.data["title"]
            == "Public Works, Procurement & Contracting "
            "Committee Meeting - 02/21/2024"
        )
        assert sdk.data["start_time"] == "2024-02-21T10:00:00-05:00"
        assert sdk.data["classification"] == "COMMITTEE"
        assert sdk.data["is_cancelled"] is False

        location = sdk.data["location"]
        assert location is not None
        assert "2079 East 9th Street" in location["address"]
        assert "Cleveland" in location["address"]

        links = sdk.data["links"]
        assert len(links) == 2
        assert any("agenda.pdf" in link["url"] for link in links)
        assert any("minutes.pdf" in link["url"] for link in links)

        await browser.close()
