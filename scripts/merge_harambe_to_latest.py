import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

try:
    from azure.storage.blob import BlobServiceClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Warning: azure-storage-blob not installed")

DEFAULT_CONTAINER = "meetings-feed-cle"
OUTPUT_BLOB = "latest.json"
UPCOMING_BLOB = "upcoming.json"
LOCAL_OUTPUT_DIR = "harambe_scrapers/output"
START_TIME_KEY = "start_time"


def get_azure_container_client(container_name: str = DEFAULT_CONTAINER):
    """Get Azure container client."""
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
    return blob_service.get_container_client(container_name)


def download_blob_from_azure(
    blob_name: str, container_name: str = DEFAULT_CONTAINER
) -> List[Dict]:
    """Download a JSON blob from Azure blob storage."""
    container_client = get_azure_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    print(f"Downloading {blob_name} from {container_name}...")

    try:
        content = blob_client.download_blob().readall().decode("utf-8")

        data = []
        for line in content.strip().split("\n"):
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Skipping invalid JSON line: {e}")
                    continue

        print(f"  Downloaded {len(data)} meetings")
        return data
    except Exception as e:
        print(f"  Failed to download {blob_name}: {e}")
        return []


def read_harambe_from_local(output_dir: str = LOCAL_OUTPUT_DIR) -> List[Dict]:
    """Read latest Harambe scraper outputs from local files."""
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"  Local output directory not found: {output_dir}")
        return []

    print(f"\nReading latest Harambe outputs from {output_dir}/...")

    by_scraper = {}

    for json_file in output_path.glob("*.json"):
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
        print(f"  No Harambe output files found in {output_dir}")
        return []

    all_meetings = []

    for scraper_name, files in by_scraper.items():
        latest = max(files, key=lambda x: x["timestamp"])

        print(f"  {scraper_name}: Using {latest['file'].name}")

        try:
            with open(latest["file"], "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        meeting = json.loads(line)
                        all_meetings.append(meeting)
        except Exception as e:
            print(f"    Error reading {latest['file'].name}: {e}")

    print(f"  Found {len(all_meetings)} Harambe meetings from local files")
    return all_meetings


def filter_out_scrapers(meetings: List[Dict], scraper_names: List[str]) -> List[Dict]:
    """Remove all meetings from specified scrapers."""
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
    blob_name: str = OUTPUT_BLOB,
    container_name: str = DEFAULT_CONTAINER,
) -> None:
    """Upload merged data to Azure blob storage."""
    container_client = get_azure_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    jsonlines_content = "\n".join(
        json.dumps(meeting, ensure_ascii=False) for meeting in data
    )
    blob_client.upload_blob(jsonlines_content, overwrite=True)

    print(f"  Uploaded to {blob_name} ({len(data)} meetings)")


def upload_scraper_files_to_azure(
    output_dir: str = LOCAL_OUTPUT_DIR,
    container_name: str = DEFAULT_CONTAINER,
) -> None:
    """Upload individual Harambe scraper output files to Azure root level."""
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"  Local output directory not found: {output_dir}")
        return

    container_client = get_azure_container_client(container_name)

    by_scraper = {}
    for json_file in output_path.glob("*.json"):
        filename = json_file.stem
        parts = filename.rsplit("_", 2)

        if len(parts) >= 3:
            scraper_name = parts[0]
            timestamp_str = f"{parts[1]}_{parts[2]}"

            if scraper_name not in by_scraper:
                by_scraper[scraper_name] = []

            by_scraper[scraper_name].append(
                {"file": json_file, "timestamp": timestamp_str}
            )

    for scraper_name, files in by_scraper.items():
        latest = max(files, key=lambda x: x["timestamp"])

        try:
            with open(latest["file"], "r") as f:
                content = f.read()

            blob_name = f"{scraper_name}.json"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(content, overwrite=True)
            print(f"  Uploaded {blob_name}")
        except Exception as e:
            print(f"  Failed to upload {scraper_name}.json: {e}")


def filter_upcoming_meetings(meetings: List[Dict]) -> List[Dict]:
    """Filter meetings to only include future meetings (start_time > yesterday)."""
    yesterday_iso = (datetime.now() - timedelta(days=1)).isoformat()[:19]

    upcoming = [
        meeting for meeting in meetings if meeting[START_TIME_KEY][:19] > yesterday_iso
    ]

    return upcoming


def main():
    print("=" * 70)
    print("Merging Harambe Scraper Outputs with Production Data")
    print("=" * 70)
    print()

    container_name = os.getenv("AZURE_CONTAINER", DEFAULT_CONTAINER)

    print("Configuration:")
    print(f"  Container: {container_name}")
    print("  Will update: latest.json, upcoming.json, and per-scraper files")
    print()

    harambe_scrapers = [
        "cle_building_standards",
        "cle_planning_commission",
        "cle_transit",
        "cuya_arts_culture",
        "cuya_county_council",
        "cuya_emergency_services_advisory",
    ]

    print(f"Harambe scrapers to process: {len(harambe_scrapers)} scrapers")
    print()

    existing_latest = download_blob_from_azure(OUTPUT_BLOB, container_name)
    existing_upcoming = download_blob_from_azure(UPCOMING_BLOB, container_name)

    harambe_meetings = read_harambe_from_local(LOCAL_OUTPUT_DIR)

    if not harambe_meetings:
        print("\nERROR: No Harambe output files found in local directory")
        print(f"  Expected location: {LOCAL_OUTPUT_DIR}")
        print("  Make sure Harambe scrapers have run before this merge step")
        exit(1)

    print("\nCleaning old Harambe data from latest.json...")
    cleaned_latest = filter_out_scrapers(existing_latest, harambe_scrapers)

    print("Cleaning old Harambe data from upcoming.json...")
    cleaned_upcoming = filter_out_scrapers(existing_upcoming, harambe_scrapers)

    harambe_upcoming = filter_upcoming_meetings(harambe_meetings)

    print("\nMerging data...")
    merged_latest = cleaned_latest + harambe_meetings
    merged_upcoming = cleaned_upcoming + harambe_upcoming

    print(
        f"  latest.json: {len(cleaned_latest)} conventional + "
        f"{len(harambe_meetings)} harambe = {len(merged_latest)} total"
    )
    print(
        f"  upcoming.json: {len(cleaned_upcoming)} conventional + "
        f"{len(harambe_upcoming)} harambe = {len(merged_upcoming)} total"
    )

    print("\nUploading merged data...")
    upload_to_azure(merged_latest, OUTPUT_BLOB, container_name)
    upload_to_azure(merged_upcoming, UPCOMING_BLOB, container_name)

    print("\nUploading individual scraper files...")
    upload_scraper_files_to_azure(LOCAL_OUTPUT_DIR, container_name)

    print()
    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
