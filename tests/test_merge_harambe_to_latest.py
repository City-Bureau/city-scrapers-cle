"""
Unit tests for scripts/merge_harambe_to_latest.py
"""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from scripts.merge_harambe_to_latest import (
    download_blob_from_azure,
    filter_out_scrapers,
    filter_upcoming_meetings,
    read_harambe_from_local,
    upload_to_azure,
)


@patch("scripts.merge_harambe_to_latest.BlobServiceClient")
def test_download_blob_from_azure(mock_blob_service):
    """Test downloading and parsing JSONLINES from Azure, skipping invalid lines."""
    mock_blob_client = Mock()
    mock_container_client = Mock()
    container = mock_blob_service.from_connection_string.return_value
    container.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client

    jsonlines = '{"id": "m1"}\nINVALID\n{"id": "m2"}'
    mock_blob_client.download_blob.return_value.readall.return_value = (
        jsonlines.encode()
    )

    with patch.dict(
        os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
    ):
        result = download_blob_from_azure("latest.json", "test-container")

    assert [m["id"] for m in result] == ["m1", "m2"]


def test_download_blob_missing_credentials():
    """Test that missing Azure credentials raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="AZURE_ACCOUNT_NAME"):
            download_blob_from_azure("latest.json", "test-container")


def test_read_harambe_from_local(tmp_path):
    """Test reading latest Harambe outputs, using newest file per scraper."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (output_dir / "cle_planning_20251110_100000.json").write_text('{"id": "old"}\n')
    (output_dir / "cle_planning_20251113_120000.json").write_text('{"id": "new"}\n')

    result = read_harambe_from_local(str(output_dir))

    assert len(result) == 1
    assert result[0]["id"] == "new"

    # Missing directory returns empty
    assert read_harambe_from_local(str(tmp_path / "nonexistent")) == []


def test_filter_out_scrapers():
    """Test filtering meetings by scraper name, supporting both id and _id fields."""
    meetings = [
        {"id": "cle_council/20251113/meeting"},
        {"id": "cle_planning/20251113/meeting"},
        {"_id": "cle_building/20251113/meeting"},
    ]

    result = filter_out_scrapers(meetings, ["cle_planning", "cle_building"])

    assert len(result) == 1
    assert result[0]["id"] == "cle_council/20251113/meeting"


def test_filter_upcoming_meetings():
    """Test filtering for future meetings, raising KeyError if start_time missing."""
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()[:19]
    yesterday = (datetime.now() - timedelta(days=2)).isoformat()[:19]

    meetings = [
        {"id": "future", "start_time": tomorrow},
        {"id": "past", "start_time": yesterday},
    ]

    result = filter_upcoming_meetings(meetings)

    assert len(result) == 1
    assert result[0]["id"] == "future"

    with pytest.raises(KeyError):
        filter_upcoming_meetings([{"id": "no_time"}])


@patch("scripts.merge_harambe_to_latest.BlobServiceClient")
def test_upload_to_azure(mock_blob_service):
    """Test uploading data to Azure in JSONLINES format."""
    mock_blob_client = Mock()
    mock_container_client = Mock()
    container = mock_blob_service.from_connection_string.return_value
    container.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client

    with patch.dict(
        os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
    ):
        upload_to_azure([{"id": "m1"}, {"id": "m2"}], "test.json", "test-container")

    uploaded = mock_blob_client.upload_blob.call_args[0][0]
    lines = uploaded.strip().split("\n")

    assert len(lines) == 2
    assert json.loads(lines[0])["id"] == "m1"
