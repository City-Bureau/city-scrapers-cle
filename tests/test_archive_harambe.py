"""Tests for scripts/archive_harambe.py"""

import os
from unittest.mock import Mock, patch

import pytest

from scripts.archive_harambe import (
    download_latest_json,
    filter_harambe_meetings,
    get_urls_to_archive,
)


@patch("scripts.archive_harambe.BlobServiceClient")
def test_download_latest_json(mock_blob_service):
    """Test downloading and parsing JSONLINES from Azure."""
    mock_blob_client = Mock()
    mock_container_client = Mock()
    blob_service = mock_blob_service.from_connection_string.return_value
    blob_service.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client

    jsonlines = '{"id": "m1"}\n{"id": "m2"}'
    mock_blob_client.download_blob.return_value.readall.return_value = (
        jsonlines.encode()
    )

    with patch.dict(
        os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "key"}
    ):
        result = download_latest_json("test-container")

    assert len(result) == 2
    assert result[0]["id"] == "m1"


def test_download_missing_credentials():
    """Test that missing Azure credentials raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="AZURE_ACCOUNT_NAME"):
            download_latest_json()


def test_filter_harambe_meetings():
    """Test filtering meetings by scraper name."""
    meetings = [
        {"extras": {"cityscrapers.org/id": "cle_city_council/2025/meeting"}},
        {"extras": {"cityscrapers.org/id": "cle_building_standards/2025/meeting"}},
        {"extras": {"cityscrapers.org/id": "cuya_county_council/2025/meeting"}},
    ]

    result = filter_harambe_meetings(
        meetings, ["cle_building_standards", "cuya_county_council"]
    )

    assert len(result) == 2


def test_filter_harambe_meetings_empty():
    """Test filtering with no matches."""
    meetings = [{"extras": {"cityscrapers.org/id": "cle_city_council/2025/meeting"}}]

    result = filter_harambe_meetings(meetings, ["cle_building_standards"])

    assert len(result) == 0


def test_get_urls_to_archive_with_legistar():
    """Test URL extraction with legistar source."""
    meeting = {
        "sources": [{"url": "https://cuyahoga.legistar.com/View.ashx?M=A&ID=123"}],
        "links": [{"url": "https://example.com/agenda.pdf"}],
        "documents": [],
    }

    urls = get_urls_to_archive(meeting)

    assert len(urls) == 2
    assert "legistar" in urls[0]
    assert urls[1] == "https://example.com/agenda.pdf"


def test_get_urls_to_archive_no_legistar():
    """Test URL extraction without legistar source (source not archived)."""
    meeting = {
        "sources": [{"url": "https://example.gov/meetings"}],
        "links": [{"url": "https://example.com/doc1.pdf"}],
        "documents": [],
    }

    urls = get_urls_to_archive(meeting)

    assert len(urls) == 1
    assert urls[0] == "https://example.com/doc1.pdf"


def test_get_urls_to_archive_calendar_excluded():
    """Test that Calendar.aspx URLs are excluded."""
    meeting = {
        "sources": [{"url": "https://cuyahoga.legistar.com/Calendar.aspx"}],
        "links": [],
        "documents": [],
    }

    urls = get_urls_to_archive(meeting)

    assert len(urls) == 0


def test_get_urls_to_archive_max_links():
    """Test that only max 3 links are sampled."""
    meeting = {
        "sources": [],
        "links": [
            {"url": "https://example.com/1.pdf"},
            {"url": "https://example.com/2.pdf"},
            {"url": "https://example.com/3.pdf"},
            {"url": "https://example.com/4.pdf"},
            {"url": "https://example.com/5.pdf"},
        ],
        "documents": [],
    }

    urls = get_urls_to_archive(meeting, max_links=3)

    assert len(urls) == 3


def test_get_urls_to_archive_empty():
    """Test URL extraction with empty meeting."""
    meeting = {"sources": [], "links": [], "documents": []}

    urls = get_urls_to_archive(meeting)

    assert len(urls) == 0
