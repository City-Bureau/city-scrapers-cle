import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from azure.storage.blob import BlobServiceClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Warning: azure-storage-blob not installed")


# Configuration Constants
DEFAULT_CONTAINER = "meetings-feed-cle"
DEFAULT_OUTPUT_BLOB = "latest_v2.json"
PRODUCTION_OUTPUT_BLOB = "latest.json"
LOCAL_OUTPUT_DIR = "harambe_scrapers/output"
HARAMBE_SCRAPERS_DIR = "harambe_scrapers"
LATEST_JSON_NAME = "latest.json"


def download_latest_from_azure(container_name: str = DEFAULT_CONTAINER) -> List[Dict]:
    """
    Download latest.json from Azure blob storage.
    This is the combined output from Scrapy's combinefeeds command.

    Args:
        container_name: Azure container name

    Returns:
        List of existing meeting dictionaries from latest.json
    """
    if not AZURE_AVAILABLE:
        raise ImportError("azure-storage-blob is required")

    account_name = os.getenv("AZURE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_ACCOUNT_KEY")

    if not account_name or not account_key:
        raise ValueError("AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY required")

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)
    blob_client = container_client.get_blob_client(LATEST_JSON_NAME)

    print(f"Downloading latest.json from {container_name}...")

    try:
        content = blob_client.download_blob().readall().decode("utf-8")

        data = []
        for line in content.strip().split("\n"):
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  ⚠ Skipping invalid JSON line: {e}")
                    continue

        print(f"  ✓ Downloaded {len(data)} existing meetings")
        return data
    except Exception as e:
        print(f"  ✗ Failed to download latest.json: {e}")
        return []


def read_harambe_from_local(output_dir: str = LOCAL_OUTPUT_DIR) -> List[Dict]:
    """
    Read latest Harambe scraper outputs from local files.
    This is faster than fetching from Azure and uses files created in the previous step.

    Handles multiple runs per scraper by selecting the latest file based on timestamp.
    File format: scraper_name_YYYYMMDD_HHMMSS.json

    Args:
        output_dir: Directory containing Harambe output JSON files

    Returns:
        List of meeting dictionaries from the latest files for each scraper
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"  ⚠ Local output directory not found: {output_dir}")
        return []

    print(f"\nReading latest Harambe outputs from {output_dir}/...")

    by_scraper = {}

    for json_file in output_path.glob("*.json"):
        # Expected format: scraper_name_YYYYMMDD_HHMMSS.json
        filename = json_file.stem
        parts = filename.rsplit("_", 2)

        if len(parts) >= 3:
            scraper_name = parts[0]
            date_part = parts[1]
            time_part = parts[2]
            timestamp_str = f"{date_part}_{time_part}"

            if scraper_name not in by_scraper:
                by_scraper[scraper_name] = []

            by_scraper[scraper_name].append(
                {"file": json_file, "timestamp": timestamp_str, "name": scraper_name}
            )

    if not by_scraper:
        print(f"  ⚠ No Harambe output files found in {output_dir}")
        return []

    all_meetings = []

    for scraper_name, files in by_scraper.items():
        latest = max(files, key=lambda x: x["timestamp"])

        print(f"  ✓ {scraper_name}: Using {latest['file'].name}")

        try:
            with open(latest["file"], "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        meeting = json.loads(line)
                        all_meetings.append(meeting)
        except Exception as e:
            print(f"    ⚠ Error reading {latest['file'].name}: {e}")

    print(f"  ✓ Found {len(all_meetings)} Harambe meetings from local files")
    return all_meetings


def get_latest_harambe_outputs(
    scraper_names: List[str], container_name: str = DEFAULT_CONTAINER
) -> List[Dict]:
    """
    Get the LATEST run output for each Harambe scraper from today.
    If multiple runs exist, only fetch the most recent one per scraper.

    Args:
        scraper_names: List of Harambe scraper names to fetch
        container_name: Azure container name

    Returns:
        List of meeting dictionaries from the latest run of each scraper
    """
    if not AZURE_AVAILABLE:
        raise ImportError("azure-storage-blob is required")

    account_name = os.getenv("AZURE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_ACCOUNT_KEY")

    if not account_name or not account_key:
        raise ValueError("AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY required")

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)

    all_meetings = []
    now = datetime.now()
    today_prefix = f"{now.year}/{now.month:02d}/{now.day:02d}"

    print(f"\nFetching latest Harambe outputs from {today_prefix}/...")

    for scraper_name in scraper_names:
        print(f"  Looking for {scraper_name}...")

        matching_blobs = []
        blobs = container_client.list_blobs(name_starts_with=today_prefix)

        for blob in blobs:
            if scraper_name in blob.name and blob.name.endswith(".json"):
                matching_blobs.append(blob)

        if not matching_blobs:
            print(f"    ⚠ No runs found for {scraper_name} today")
            continue

        latest_blob = max(matching_blobs, key=lambda b: b.last_modified)
        print(f"    ✓ Using {latest_blob.name} (modified: {latest_blob.last_modified})")

        blob_client = container_client.get_blob_client(latest_blob.name)
        content = blob_client.download_blob().readall().decode("utf-8")

        for line in content.strip().split("\n"):
            if line:
                try:
                    meeting = json.loads(line)
                    all_meetings.append(meeting)
                except json.JSONDecodeError as e:
                    print(f"    ⚠ Failed to parse line: {e}")

    print(f"  ✓ Found {len(all_meetings)} Harambe meetings total")
    return all_meetings


def filter_out_scrapers(meetings: List[Dict], scraper_names: List[str]) -> List[Dict]:
    """
    Remove all meetings from specified scrapers.

    Args:
        meetings: List of meeting dictionaries to filter
        scraper_names: List of scraper names to remove

    Returns:
        Filtered list of meetings excluding those from specified scrapers
    """
    filtered = []
    removed_count = 0

    for meeting in meetings:
        meeting_id = meeting.get("id") or meeting.get("_id", "")
        is_harambe = any(scraper_name in meeting_id for scraper_name in scraper_names)

        if not is_harambe:
            filtered.append(meeting)
        else:
            removed_count += 1

    if removed_count > 0:
        print(f"  Removed {removed_count} old Harambe meetings")

    return filtered


def upload_to_azure(
    data: List[Dict],
    blob_name: str = DEFAULT_OUTPUT_BLOB,
    container_name: str = DEFAULT_CONTAINER,
) -> None:
    """
    Upload merged data to Azure blob storage.

    Args:
        data: List of meeting dictionaries to upload
        blob_name: Name of the blob to create/overwrite
        container_name: Azure container name
    """
    if not AZURE_AVAILABLE:
        raise ImportError("azure-storage-blob is required")

    account_name = os.getenv("AZURE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_ACCOUNT_KEY")

    if not account_name or not account_key:
        raise ValueError("AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY required")

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    jsonlines_content = "\n".join(
        json.dumps(meeting, ensure_ascii=False) for meeting in data
    )
    blob_client.upload_blob(jsonlines_content, overwrite=True)

    print(f"\n✓ Uploaded to {blob_name} ({len(data)} meetings)")


def discover_harambe_scrapers_from_files(
    scrapers_dir: str = HARAMBE_SCRAPERS_DIR,
) -> List[str]:
    """
    Discover Harambe scrapers by reading SCRAPER_NAME from Python files.
    This provides a fallback when Azure auto-detection fails.

    Args:
        scrapers_dir: Directory containing Harambe scraper Python files

    Returns:
        List of discovered scraper names from SCRAPER_NAME constants
    """
    scrapers = []
    scrapers_path = Path(scrapers_dir)

    if not scrapers_path.exists():
        print(f"  ⚠ Harambe scrapers directory not found: {scrapers_dir}")
        return []

    for py_file in scrapers_path.glob("*.py"):
        if py_file.name in ["__init__.py", "observers.py", "utils.py"]:
            continue

        try:
            with open(py_file, "r") as f:
                content = f.read()
                match = re.search(r'SCRAPER_NAME\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    scraper_name = match.group(1)
                    scrapers.append(scraper_name)
        except Exception as e:
            print(f"  ⚠ Error reading {py_file.name}: {e}")

    return scrapers


def auto_detect_harambe_scrapers(container_name: str = DEFAULT_CONTAINER) -> List[str]:
    """
    Auto-detect Harambe scrapers by looking for _v2 blobs in today's uploads.
    Falls back to filesystem discovery if Azure detection fails.

    Args:
        container_name: Azure container name

    Returns:
        List of detected Harambe scraper names from Azure blobs
    """
    if not AZURE_AVAILABLE:
        return []

    account_name = os.getenv("AZURE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_ACCOUNT_KEY")

    if not account_name or not account_key:
        return []

    try:
        conn_str = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={account_key};"
            f"EndpointSuffix=core.windows.net"
        )

        blob_service = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service.get_container_client(container_name)

        now = datetime.now()
        today_prefix = f"{now.year}/{now.month:02d}/{now.day:02d}"

        scrapers = set()
        blobs = container_client.list_blobs(name_starts_with=today_prefix)

        for blob in blobs:
            if "_v2" in blob.name and blob.name.endswith(".json"):
                parts = blob.name.split("/")
                if len(parts) >= 5:
                    filename = parts[-1]
                    scraper_name = filename.replace(".json", "")
                    scrapers.add(scraper_name)

        return list(scrapers)
    except Exception as e:
        print(f"  ⚠ Azure auto-detection failed: {e}")
        return []


def main():
    print("=" * 70)
    print("Merging Harambe Scraper Outputs with Production latest.json")
    print("=" * 70)
    print()

    container_name = os.getenv("AZURE_CONTAINER", DEFAULT_CONTAINER)
    output_blob = os.getenv("OUTPUT_BLOB", DEFAULT_OUTPUT_BLOB)

    print("Configuration:")
    print(f"  Container: {container_name}")
    print(f"  Output blob: {output_blob}")
    if output_blob == "latest_v2.json":
        print(f"  ⚠ Using TEST mode - outputs to {output_blob}")
        print("  💡 Set OUTPUT_BLOB=latest.json for production cutover")
    else:
        print(f"  ⚠ PRODUCTION mode - will overwrite {output_blob}!")
    print()

    harambe_scrapers = auto_detect_harambe_scrapers(container_name)

    if harambe_scrapers:
        print(f"Auto-detected Harambe scrapers from Azure: {harambe_scrapers}")
    else:
        print("  Azure auto-detection returned no scrapers, checking filesystem...")
        harambe_scrapers = discover_harambe_scrapers_from_files(HARAMBE_SCRAPERS_DIR)
        if harambe_scrapers:
            print(f"Discovered Harambe scrapers from files: {harambe_scrapers}")
        else:
            print("  ⚠ Warning: No Harambe scrapers found!")
            print("  The merge will only include conventional scraper data.")

    print()

    existing_meetings = download_latest_from_azure(container_name)

    if not existing_meetings:
        print("\n⚠ Warning: No existing meetings found in latest.json")
        print("This might be normal if combinefeeds hasn't run yet.")
        print()

    print("\nCleaning old Harambe data...")
    cleaned_meetings = filter_out_scrapers(existing_meetings, harambe_scrapers)

    harambe_meetings = read_harambe_from_local(LOCAL_OUTPUT_DIR)

    if not harambe_meetings:
        print("\n  ⚠ No local files found, fetching from Azure...")
        harambe_meetings = get_latest_harambe_outputs(harambe_scrapers, container_name)

    print("\nMerging data...")
    merged = cleaned_meetings + harambe_meetings

    print(f"  Conventional scrapers: {len(cleaned_meetings)} meetings")
    print(f"  Harambe scrapers: {len(harambe_meetings)} meetings")
    print(f"  Total merged: {len(merged)} meetings")

    upload_to_azure(merged, blob_name=output_blob, container_name=container_name)

    print()
    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
