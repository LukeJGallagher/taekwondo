"""
Download rankings data from Azure Blob Storage to local data folder
Run this after GitHub Actions scraper completes to sync data to dashboard
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def download_azure_data():
    """Download all CSV files from Azure Blob Storage"""

    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("Installing azure-storage-blob...")
        os.system("pip install azure-storage-blob")
        from azure.storage.blob import BlobServiceClient

    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')

    if not connection_string:
        print("ERROR: No Azure connection string found in .env")
        print("Set AZURE_STORAGE_CONNECTION_STRING in your .env file")
        return False

    print("=" * 60)
    print("AZURE DATA SYNC")
    print("=" * 60)

    try:
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container = blob_service.get_container_client('taekwondo-data')

        # Create local data directories
        data_dir = Path('data')
        rankings_dir = data_dir / 'rankings'
        rankings_dir.mkdir(parents=True, exist_ok=True)

        # List all blobs
        print("\nFetching blob list from Azure...")
        blobs = list(container.list_blobs())

        if not blobs:
            print("No data found in Azure container 'taekwondo-data'")
            return False

        print(f"Found {len(blobs)} files in Azure")

        downloaded = 0
        for blob in blobs:
            blob_name = blob.name
            print(f"\n  Downloading: {blob_name}")

            # Determine local path
            if '/' in blob_name:
                folder, filename = blob_name.rsplit('/', 1)
                local_folder = data_dir / folder
            else:
                local_folder = data_dir
                filename = blob_name

            local_folder.mkdir(parents=True, exist_ok=True)
            local_path = local_folder / filename

            # Download blob
            blob_client = container.get_blob_client(blob_name)
            with open(local_path, 'wb') as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())

            # Show file size
            size = local_path.stat().st_size
            print(f"    Saved: {local_path} ({size:,} bytes)")
            downloaded += 1

        print(f"\n{'=' * 60}")
        print(f"SYNC COMPLETE: Downloaded {downloaded} files")
        print(f"{'=' * 60}")

        # Update world_rankings_latest.csv if we got new data
        latest_rankings = list(rankings_dir.glob('world_rankings_*.csv'))
        if latest_rankings:
            # Sort by modification time and copy the newest to latest
            latest_rankings.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            newest = latest_rankings[0]
            latest_path = rankings_dir / 'world_rankings_latest.csv'

            import shutil
            shutil.copy(newest, latest_path)
            print(f"\nUpdated world_rankings_latest.csv from {newest.name}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_local_data_summary():
    """Show what data we have locally"""
    print("\n" + "=" * 60)
    print("LOCAL DATA SUMMARY")
    print("=" * 60)

    data_dir = Path('data')

    # Check rankings
    rankings_dir = data_dir / 'rankings'
    if rankings_dir.exists():
        csv_files = list(rankings_dir.glob('*.csv'))
        print(f"\nRankings folder: {len(csv_files)} files")
        for f in csv_files:
            # Count rows
            try:
                import pandas as pd
                df = pd.read_csv(f)
                categories = df['weight_category'].unique() if 'weight_category' in df.columns else ['unknown']
                print(f"  - {f.name}: {len(df)} athletes, categories: {', '.join(categories)}")
            except:
                print(f"  - {f.name}")
    else:
        print("\nNo rankings folder found")

    # Check athletes
    athletes_dir = data_dir / 'athletes'
    if athletes_dir.exists():
        csv_files = list(athletes_dir.glob('*.csv'))
        print(f"\nAthletes folder: {len(csv_files)} files")
        for f in csv_files:
            try:
                import pandas as pd
                df = pd.read_csv(f)
                print(f"  - {f.name}: {len(df)} records")
            except:
                print(f"  - {f.name}")

    # Check competitions
    comp_dir = data_dir / 'competitions'
    if comp_dir.exists():
        csv_files = list(comp_dir.glob('*.csv'))
        print(f"\nCompetitions folder: {len(csv_files)} files")


if __name__ == '__main__':
    # Show current local data
    show_local_data_summary()

    print("\n")

    # Download from Azure
    success = download_azure_data()

    if success:
        # Show updated local data
        show_local_data_summary()
        print("\nDashboard will now show updated data!")
        print("Refresh your browser at http://localhost:8505")
    else:
        print("\nSync failed - check your Azure connection string")
