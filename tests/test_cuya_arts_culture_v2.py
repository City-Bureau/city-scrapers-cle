"""
Unit tests for Cuyahoga County Arts & Culture v2 scraper (Harambe-based).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import async_playwright

from harambe_scrapers.cuya_arts_culture import (
    AGENCY_NAME,
    SCRAPER_NAME,
    START_URL,
    main,
    scrape,
)


@pytest.mark.asyncio
async def test_scraper_with_real_browser_and_html_fixtures():
    """
    Integration test using real browser with HTML fixtures.
    Loads real HTML, runs scraper, and asserts parsed data.
    """
    materials_path = (
        Path(__file__).parent / "files" / "cuya_arts_culture_materials.html"
    )
    schedule_path = Path(__file__).parent / "files" / "cuya_arts_culture_schedule.html"

    with open(materials_path, "r", encoding="utf-8") as f:
        materials_html = f.read()
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_html = f.read()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        sdk = MagicMock()
        sdk.save_data = AsyncMock()

        async def goto_with_fixture(url, **kwargs):
            if "board-materials" in url:
                await page.set_content(materials_html)
            elif "board-meeting-schedule" in url:
                await page.set_content(schedule_html)

        page.goto = goto_with_fixture
        sdk.page = page

        await scrape(sdk, START_URL, {})
        await browser.close()

    msg = f"Expected meetings from HTML, got {sdk.save_data.call_count}"
    assert sdk.save_data.call_count >= 3, msg

    all_meetings = [call[0][0] for call in sdk.save_data.call_args_list]

    meeting_titles = [m["name"] for m in all_meetings]
    assert "CAC Board of Trustees Regular Meeting" in meeting_titles
    assert "CAC Board of Trustees Annual Meeting" in meeting_titles
    assert "CAC Board of Trustees Special Meeting" in meeting_titles

    feb_15_meetings = [m for m in all_meetings if "2024-02-15" in m["start_time"]]
    dates = [m["start_time"][:10] for m in all_meetings]
    msg = f"Should find February 15, 2024 meeting. Found: {dates}"
    assert len(feb_15_meetings) >= 1, msg

    feb_15 = feb_15_meetings[0]
    assert feb_15["name"] == "CAC Board of Trustees Regular Meeting"
    assert feb_15["extras"]["cityscrapers.org/agency"] == AGENCY_NAME
    assert feb_15["timezone"] == "America/New_York"
    assert "2024-02-15" in feb_15["start_time"]
    assert "T16:00" in feb_15["start_time"]
    assert "Children's Museum of Cleveland" in feb_15["location"]["name"]
    assert "44115" in feb_15["extras"]["cityscrapers.org/address"]
    assert feb_15["classification"] == "BOARD"
    assert "links" in feb_15
    assert isinstance(feb_15["links"], list)

    april_17_meetings = [m for m in all_meetings if "2024-04-17" in m["start_time"]]
    assert len(april_17_meetings) >= 1
    april_17 = april_17_meetings[0]
    assert april_17["name"] == "CAC Board of Trustees Annual Meeting"
    assert "Cleveland Public Library" in april_17["location"]["name"]

    april_29_meetings = [m for m in all_meetings if "2024-04-29" in m["start_time"]]
    assert len(april_29_meetings) >= 1
    april_29 = april_29_meetings[0]
    assert april_29["name"] == "CAC Board of Trustees Special Meeting"


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function orchestration"""
    with patch("harambe_scrapers.cuya_arts_culture.SDK.run") as mock_run:
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
    assert SCRAPER_NAME == "cuya_arts_culture_v2"
    assert AGENCY_NAME == "Cuyahoga County Arts & Culture"
    url = "https://www.cacgrants.org/about-us/meet-our-board/board-meeting-schedule/"
    assert START_URL == url
