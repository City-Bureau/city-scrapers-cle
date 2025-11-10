"""
Unit tests for Cleveland City Planning Commission v2 scraper (Harambe-based).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import async_playwright

from harambe_scrapers.cle_planning_commission import (
    AGENCY_NAME,
    SCRAPER_NAME,
    START_URL,
    main,
    scrape,
)


@pytest.mark.asyncio
async def test_scraper_with_real_browser_and_html_fixture():
    """
    Integration test using real browser with HTML fixture.
    Loads real HTML, runs scraper, and asserts parsed data.
    """
    fixture_path = Path(__file__).parent / "files" / "cle_planning_commission.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_html = f.read()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_html)

        sdk = MagicMock()
        sdk.save_data = AsyncMock()
        sdk.page = page

        await scrape(sdk, START_URL, {})
        await browser.close()

    msg = f"Expected meetings from HTML fixture, got {sdk.save_data.call_count}"
    assert sdk.save_data.call_count >= 3, msg

    all_meetings = [call[0][0] for call in sdk.save_data.call_args_list]

    unique_titles = set(m["name"] for m in all_meetings)
    assert "CITY PLANNING COMMISSION" in unique_titles

    meeting_dates = [m["start_time"][:10] for m in all_meetings]
    assert "2025-01-03" in meeting_dates or "2025-01-17" in meeting_dates
    assert "2025-02-07" in meeting_dates or "2025-02-21" in meeting_dates
    assert "2025-03-07" in meeting_dates or "2025-03-21" in meeting_dates

    for meeting in all_meetings[:3]:
        assert meeting["_type"] == "event"
        assert meeting["name"] == "CITY PLANNING COMMISSION"
        assert meeting["extras"]["cityscrapers.org/agency"] == AGENCY_NAME
        assert meeting["timezone"] == "America/Detroit"
        assert "classification" in meeting
        assert "location" in meeting


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function orchestration"""
    with patch("harambe_scrapers.cle_planning_commission.SDK.run") as mock_run:
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            with patch("builtins.open", create=True):
                mock_run.return_value = None

                await main()

                mock_mkdir.assert_called_once_with(exist_ok=True)
                mock_run.assert_called_once()
                call_args = mock_run.call_args

                assert "observer" in call_args[1]
                assert "harness" in call_args[1]
                assert call_args[1]["headless"] is True


def test_scraper_configuration():
    """Test scraper configuration constants"""
    assert SCRAPER_NAME == "cle_planning_commission_v2"
    assert AGENCY_NAME == "Cleveland City Planning Commission"
    url = "https://planning.clevelandohio.gov/designreview/schedule.php"
    assert START_URL == url
