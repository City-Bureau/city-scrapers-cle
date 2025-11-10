"""
Unit tests for Cleveland Board of Building Standards v2 scraper (Harambe-based).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import async_playwright

from harambe_scrapers.cle_building_standards import AGENCY_NAME, START_URL, main, scrape


@pytest.mark.asyncio
async def test_scraper_with_real_browser_and_html_fixture():
    """
    Integration test using real browser with HTML fixture.
    Loads real HTML, runs scraper, and asserts parsed data.
    """
    fixture_path = Path(__file__).parent / "files" / "cle_building_standards.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_html = f.read()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(fixture_html)

        sdk = MagicMock()
        sdk.save_data = AsyncMock()
        sdk.page = page

        async def mock_goto(url, **kwargs):
            await page.set_content(fixture_html)

        page.goto = mock_goto

        await scrape(sdk, START_URL, {})
        await browser.close()

    msg = f"Expected meetings from HTML fixture, got {sdk.save_data.call_count}"
    assert sdk.save_data.call_count >= 3, msg

    all_meetings = [call[0][0] for call in sdk.save_data.call_args_list]

    meeting_dates = [m["start_time"][:10] for m in all_meetings]
    assert "2019-10-02" in meeting_dates
    assert "2019-09-18" in meeting_dates
    assert "2019-09-04" in meeting_dates

    for meeting in all_meetings[:3]:
        assert meeting["_type"] == "event"
        assert meeting["extras"]["cityscrapers.org/agency"] == AGENCY_NAME
        assert meeting["timezone"] == "America/Detroit"
        assert "classification" in meeting
        assert "location" in meeting
        assert "start_time" in meeting


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function orchestration"""
    with patch("harambe_scrapers.cle_building_standards.SDK.run") as mock_run:
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
