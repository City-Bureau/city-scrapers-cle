"""
Unit tests for scripts/merge_harambe_to_latest.py

Tests all core functionality including:
- JSONLINES parsing for download/upload
- Local file reading with latest selection
- Azure blob fetching
- Scraper filtering
- Dynamic scraper discovery
"""

import json
import os
from unittest.mock import Mock, patch

import pytest

from scripts.merge_harambe_to_latest import (
    discover_harambe_scrapers_from_files,
    download_latest_from_azure,
    filter_out_scrapers,
    read_harambe_from_local,
    upload_to_azure,
)


class TestDownloadLatestFromAzure:
    """Test downloading and parsing latest.json in JSONLINES format."""

    @patch("scripts.merge_harambe_to_latest.BlobServiceClient")
    def test_download_jsonlines_format(self, mock_blob_service):
        mock_blob_client = Mock()
        mock_container_client = Mock()
        container = mock_blob_service.from_connection_string.return_value
        container.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client

        jsonlines = (
            '{"id": "meeting1", "title": "Meeting 1"}\n'
            '{"id": "meeting2", "title": "Meeting 2"}\n'
            '{"id": "meeting3", "title": "Meeting 3"}'
        )
        mock_blob_client.download_blob.return_value.readall.return_value = (
            jsonlines.encode("utf-8")
        )

        with patch.dict(
            os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
        ):
            result = download_latest_from_azure("test-container")

        assert len(result) == 3
        assert result[0]["id"] == "meeting1"
        assert result[1]["id"] == "meeting2"
        assert result[2]["id"] == "meeting3"

    @patch("scripts.merge_harambe_to_latest.BlobServiceClient")
    def test_download_empty_file(self, mock_blob_service):
        mock_blob_client = Mock()
        mock_container_client = Mock()
        container = mock_blob_service.from_connection_string.return_value
        container.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.return_value.readall.return_value = b""

        with patch.dict(
            os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
        ):
            result = download_latest_from_azure("test-container")

        assert result == []

    @patch("scripts.merge_harambe_to_latest.BlobServiceClient")
    def test_download_with_invalid_lines(self, mock_blob_service):
        mock_blob_client = Mock()
        mock_container_client = Mock()
        container = mock_blob_service.from_connection_string.return_value
        container.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client

        jsonlines = (
            '{"id": "meeting1", "title": "Meeting 1"}\n'
            "INVALID JSON LINE\n"
            '{"id": "meeting2", "title": "Meeting 2"}'
        )
        mock_blob_client.download_blob.return_value.readall.return_value = (
            jsonlines.encode("utf-8")
        )

        with patch.dict(
            os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
        ):
            result = download_latest_from_azure("test-container")

        assert len(result) == 2
        assert result[0]["id"] == "meeting1"
        assert result[1]["id"] == "meeting2"

    def test_download_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AZURE_ACCOUNT_NAME"):
                download_latest_from_azure("test-container")


class TestReadHarambeFromLocal:
    """Test reading Harambe scraper outputs from local files."""

    def test_read_latest_files(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        (output_dir / "cle_planning_20251110_100000.json").write_text(
            '{"id": "old1", "name": "Old Meeting"}\n'
        )
        (output_dir / "cle_planning_20251113_120000.json").write_text(
            '{"id": "new1", "name": "New Meeting 1"}\n'
            '{"id": "new2", "name": "New Meeting 2"}\n'
        )

        result = read_harambe_from_local(str(output_dir))

        assert len(result) == 2
        assert result[0]["id"] == "new1"
        assert result[1]["id"] == "new2"

    def test_read_multiple_scrapers(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        (output_dir / "cle_planning_20251113_120000.json").write_text(
            '{"id": "planning1"}\n'
        )
        (output_dir / "cle_building_20251113_120000.json").write_text(
            '{"id": "building1"}\n'
        )

        result = read_harambe_from_local(str(output_dir))

        assert len(result) == 2
        ids = [m["id"] for m in result]
        assert "planning1" in ids
        assert "building1" in ids

    def test_read_missing_directory(self, tmp_path):
        result = read_harambe_from_local(str(tmp_path / "nonexistent"))
        assert result == []

    def test_read_empty_directory(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = read_harambe_from_local(str(output_dir))
        assert result == []


class TestFilterOutScrapers:
    """Test filtering meetings by scraper name."""

    def test_filter_harambe_scrapers(self):
        meetings = [
            {"id": "cle_city_council/20251113/1400/meeting"},
            {"id": "cle_planning/20251113/1400/meeting"},
            {"id": "cle_building_standards/20251113/1500/meeting"},
            {"id": "cle_landmarks/20251113/1600/meeting"},
        ]

        scrapers_to_remove = ["cle_planning", "cle_building_standards"]
        result = filter_out_scrapers(meetings, scrapers_to_remove)

        assert len(result) == 2
        assert result[0]["id"] == "cle_city_council/20251113/1400/meeting"
        assert result[1]["id"] == "cle_landmarks/20251113/1600/meeting"

    def test_filter_no_matches(self):
        meetings = [
            {"id": "cle_city_council/20251113/1400/meeting"},
            {"id": "cle_landmarks/20251113/1600/meeting"},
        ]

        result = filter_out_scrapers(meetings, ["cle_planning"])

        assert len(result) == 2

    def test_filter_all_matches(self):
        meetings = [
            {"id": "cle_planning/20251113/1400/meeting"},
            {"id": "cle_building/20251113/1500/meeting"},
        ]

        result = filter_out_scrapers(meetings, ["cle_planning", "cle_building"])

        assert len(result) == 0

    def test_filter_with_underscore_id_field(self):
        meetings = [
            {"_id": "cle_planning/20251113/1400/meeting"},
        ]

        result = filter_out_scrapers(meetings, ["cle_planning"])
        assert len(result) == 0


class TestUploadToAzure:
    """Test uploading merged data to Azure in JSONLINES format."""

    @patch("scripts.merge_harambe_to_latest.BlobServiceClient")
    def test_upload_jsonlines_format(self, mock_blob_service):
        mock_blob_client = Mock()
        mock_container_client = Mock()
        container = mock_blob_service.from_connection_string.return_value
        container.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client

        data = [
            {"id": "meeting1", "title": "Meeting 1"},
            {"id": "meeting2", "title": "Meeting 2"},
        ]

        with patch.dict(
            os.environ, {"AZURE_ACCOUNT_NAME": "test", "AZURE_ACCOUNT_KEY": "test"}
        ):
            upload_to_azure(data, "test.json", "test-container")

        assert mock_blob_client.upload_blob.called
        uploaded_content = mock_blob_client.upload_blob.call_args[0][0]

        lines = uploaded_content.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == "meeting1"
        assert json.loads(lines[1])["id"] == "meeting2"


class TestDiscoverHarambeScrapersFromFiles:
    """Test discovering scraper names from Python files."""

    def test_discover_from_files(self, tmp_path):
        scrapers_dir = tmp_path / "harambe_scrapers"
        scrapers_dir.mkdir()

        (scrapers_dir / "cle_planning.py").write_text('SCRAPER_NAME = "cle_planning"\n')
        (scrapers_dir / "cle_building.py").write_text("SCRAPER_NAME = 'cle_building'\n")
        (scrapers_dir / "__init__.py").write_text("")  # Should be skipped

        result = discover_harambe_scrapers_from_files(str(scrapers_dir))

        assert len(result) == 2
        assert "cle_planning" in result
        assert "cle_building" in result

    def test_discover_missing_directory(self, tmp_path):
        result = discover_harambe_scrapers_from_files(str(tmp_path / "nonexistent"))
        assert result == []

    def test_discover_skip_utility_files(self, tmp_path):
        scrapers_dir = tmp_path / "harambe_scrapers"
        scrapers_dir.mkdir()

        (scrapers_dir / "observers.py").write_text('SCRAPER_NAME = "should_skip"\n')
        (scrapers_dir / "utils.py").write_text('SCRAPER_NAME = "should_skip"\n')
        (scrapers_dir / "cle_real.py").write_text('SCRAPER_NAME = "cle_real"\n')

        result = discover_harambe_scrapers_from_files(str(scrapers_dir))

        assert len(result) == 1
        assert "cle_real" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
