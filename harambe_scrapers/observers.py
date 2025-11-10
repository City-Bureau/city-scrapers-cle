"""
Simple data collection observers for Harambe scrapers.

Collects scraped data and optionally uploads to Azure Blob Storage
in a format compatible with Scrapy infrastructure.
"""

import json
import os
from datetime import datetime
from typing import Any

try:
    from azure.storage.blob import BlobServiceClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class DataCollector:
    """
    Simple observer that collects data and optionally uploads to Azure.

    Usage:
        observer = DataCollector(
            scraper_name="cle_planning_commission",
            timezone="America/Detroit"
        )
        await SDK.run(
            scrape_func, url, observer=observer, harness=playwright_harness
        )
    """

    def __init__(self, scraper_name: str, timezone: str = "America/Detroit"):
        self.scraper_name = scraper_name
        self.timezone = timezone
        self.data = []
        self.azure_client = self._init_azure()
        # Store run start time to ensure all meetings go to same blob
        self.run_start_time = datetime.now()

    def _init_azure(self):
        """Initialize Azure client if credentials available."""
        if not AZURE_AVAILABLE:
            return None

        account_name = os.getenv("AZURE_ACCOUNT_NAME")
        account_key = os.getenv("AZURE_ACCOUNT_KEY")
        container = os.getenv("AZURE_CONTAINER")

        if account_name and account_key and container:
            try:
                conn_str = (
                    f"DefaultEndpointsProtocol=https;"
                    f"AccountName={account_name};"
                    f"AccountKey={account_key};"
                    f"EndpointSuffix=core.windows.net"
                )
                return BlobServiceClient.from_connection_string(
                    conn_str
                ).get_container_client(container)
            except Exception as e:
                print(f"Azure init failed: {e}")
        return None

    async def on_save_data(self, data: dict[str, Any]):
        """Save data and upload to Azure if configured."""
        self.data.append(data)
        print(f"  ✓ {data.get('start_time', '')[:10]} - {data.get('name', 'Unknown')}")

        if self.azure_client:
            self._upload_to_azure(data)

    def _upload_to_azure(self, data: dict[str, Any]):
        """Upload to Azure in jsonlines format matching Scrapy pattern."""
        try:
            # Use run start time so all meetings from this run go to same blob
            blob_path = (
                f"{self.run_start_time.year}/{self.run_start_time.month:02d}/"
                f"{self.run_start_time.day:02d}/"
                f"{self.run_start_time.hour:02d}{self.run_start_time.minute:02d}/"
                f"{self.scraper_name}.json"
            )
            blob_client = self.azure_client.get_blob_client(blob_path)

            # Remove __url field if it exists (added by Harambe SDK)
            clean_data = {k: v for k, v in data.items() if k != "__url"}

            # Jsonlines format
            json_line = json.dumps(clean_data, ensure_ascii=False) + "\n"
            try:
                existing = blob_client.download_blob().readall().decode("utf-8")
                blob_client.upload_blob(existing + json_line, overwrite=True)
            except Exception:  # Blob doesn't exist yet
                blob_client.upload_blob(json_line)
        except Exception as e:
            print(f"  Azure upload failed: {e}")

    async def on_queue_url(self, url, context, options):
        pass

    async def on_download(self, *args):
        return {}

    async def on_paginate(self, url):
        pass

    async def on_save_cookies(self, cookies):
        pass

    async def on_save_local_storage(self, storage):
        pass
