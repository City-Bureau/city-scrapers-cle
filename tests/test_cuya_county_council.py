"""
Unit tests for Cuyahoga County Council scraper.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from playwright.async_api import async_playwright

from harambe_scrapers.cuya_county_council import DetailSDK, ListingSDK
from harambe_scrapers.extractor.cuya_county_council.detail import (
    scrape as detail_scrape,
)
from harambe_scrapers.extractor.cuya_county_council.listing import (
    scrape as listing_scrape,
)


@pytest.fixture
def fixture_json():
    parent_dir = Path(__file__).parent
    fixture_path = parent_dir / "files" / "cuya_county_council.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_listing_scraper_parses_json_api_and_generates_urls(fixture_json):
    """Test listing scraper parses JSON API and generates event URLs correctly"""
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


@pytest.fixture
def fixture_detail_html():
    parent_dir = Path(__file__).parent
    fixture_path = parent_dir / "files" / "cuya_county_council_detail.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.mark.asyncio
async def test_detail_scraper_extracts_meeting_data_from_html(fixture_detail_html):
    """Test detail scraper extracts title, location, and links from HTML"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_detail_html)

        sdk = DetailSDK(page)
        # Context data that would normally come from the listing scraper
        context = {
            "title": "Committee of the Whole Meeting/Executive Session - 01/09/2024",
            "description": "Regular committee meeting to discuss county business",
            "start_time": "2024-01-09T15:00:00-05:00",
            "is_all_day_event": False,
        }

        await detail_scrape(
            sdk,
            (
                "https://cuyahogacounty.gov/council/council-event-details/"
                "2024/01/09/council/committee-of-the-whole-meeting---01-09-2024"
            ),
            context,
        )

        assert sdk.data is not None

        assert (
            sdk.data["title"]
            == "Committee of the Whole Meeting/Executive Session - 01/09/2024"
        )
        assert sdk.data["start_time"] == "2024-01-09T15:00:00-05:00"

        location = sdk.data["location"]
        assert location is not None
        assert "2079 East 9th Street" in location["address"]
        assert "Cleveland" in location["address"]

        links = sdk.data["links"]
        assert len(links) == 3
        assert any("Agenda" in link["title"] for link in links)
        assert any("Minutes" in link["title"] for link in links)
        assert any("Legislation" in link["title"] for link in links)
        assert any("20240109-ccwhl-agenda.pdf" in link["url"] for link in links)

        assert sdk.data["classification"] == "COMMITTEE"
        assert sdk.data["is_cancelled"] is False

        await browser.close()
