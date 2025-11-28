"""
Unit tests for observer classes (DataCollector).
"""

from unittest.mock import MagicMock, patch

import pytest

from harambe_scrapers.observers import DataCollector


@pytest.fixture
def mock_azure_env():
    with patch.dict(
        "os.environ",
        {
            "AZURE_ACCOUNT_NAME": "testaccount",
            "AZURE_ACCOUNT_KEY": "testkey",
            "AZURE_CONTAINER": "testcontainer",
        },
    ):
        yield


@pytest.mark.asyncio
@patch("harambe_scrapers.observers.BlobServiceClient")
async def test_data_collector_with_azure(mock_blob_client, mock_azure_env):
    """Test DataCollector with Azure configuration"""
    mock_container = MagicMock()
    mock_blob = MagicMock()
    mock_blob.download_blob.side_effect = Exception("Not found")
    mock_blob.upload_blob = MagicMock()
    mock_container.get_blob_client.return_value = mock_blob
    blob_client = mock_blob_client.from_connection_string.return_value
    blob_client.get_container_client.return_value = mock_container

    collector = DataCollector("cle_planning_commission", "America/Detroit")

    test_data = {"name": "Test Meeting", "start_time": "2025-01-15T09:00:00-05:00"}

    await collector.on_save_data(test_data)

    assert mock_container.get_blob_client.called
    assert mock_blob.upload_blob.called

    blob_path_call = mock_container.get_blob_client.call_args[0][0]
    assert "cle_planning_commission.json" in blob_path_call
    assert blob_path_call.count("/") == 4


@pytest.mark.asyncio
async def test_data_collector_without_azure():
    """Test DataCollector without Azure configuration"""
    collector = DataCollector("test_scraper", "America/Detroit")

    assert collector.scraper_name == "test_scraper"
    assert collector.timezone == "America/Detroit"
    assert collector.data == []
    assert collector.run_start_time is not None


@pytest.mark.asyncio
async def test_on_save_data():
    """Test saving data to collector"""
    collector = DataCollector("test_scraper", "America/Detroit")
    test_data = {
        "name": "Test Meeting",
        "start_time": "2025-01-15T09:00:00-05:00",
        "classification": "Board",
    }

    await collector.on_save_data(test_data)

    assert len(collector.data) == 1
    assert collector.data[0] == test_data


@pytest.mark.asyncio
async def test_on_save_data_multiple():
    """Test saving multiple data items"""
    collector = DataCollector("test_scraper", "America/Detroit")
    test_data_1 = {"name": "Meeting 1", "start_time": "2025-01-15T09:00:00-05:00"}
    test_data_2 = {"name": "Meeting 2", "start_time": "2025-01-16T09:00:00-05:00"}

    await collector.on_save_data(test_data_1)
    await collector.on_save_data(test_data_2)

    assert len(collector.data) == 2
    assert collector.data[0]["name"] == "Meeting 1"
    assert collector.data[1]["name"] == "Meeting 2"
