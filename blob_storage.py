"""
Azure Blob Storage Module for Taekwondo Analytics
Supports Parquet files with DuckDB queries for fast analysis

Usage:
    from blob_storage import load_data, query, save_data

    # Load all data
    df = load_data()

    # SQL queries with DuckDB
    result = query("SELECT * FROM rankings WHERE country = 'KSA'")

    # Save data
    save_data(df, append=True)
"""

import os
import sys
import io
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

# UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Azure imports
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Warning: azure-storage-blob not installed. Run: pip install azure-storage-blob")

# DuckDB import
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print("Warning: duckdb not installed. Run: pip install duckdb")


# =============================================================================
# CONFIGURATION - Taekwondo Analytics
# =============================================================================

CONTAINER_NAME = "taekwondo-data"
STORAGE_ACCOUNT_URL = "https://teamsaudianalytics.blob.core.windows.net/"

# Data file paths in Azure Blob
BLOB_PATHS = {
    'rankings': 'rankings/world_rankings_latest.parquet',
    'rankings_history': 'rankings/history/',
    'competitions': 'competitions/competitions_master.parquet',
    'matches': 'matches/matches_master.parquet',
    'athletes': 'athletes/athletes_master.parquet',
    'scouting': 'scouting/scouting_profiles.parquet',
}

# =============================================================================
# CONNECTION MANAGEMENT
# =============================================================================

_CONN_STRING = None


def _get_connection_string() -> Optional[str]:
    """Get Azure Storage connection string from env or Streamlit secrets."""
    global _CONN_STRING

    if _CONN_STRING is not None:
        return _CONN_STRING

    # Try environment variable
    _CONN_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    # Try Streamlit secrets
    if not _CONN_STRING:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'AZURE_STORAGE_CONNECTION_STRING' in st.secrets:
                _CONN_STRING = st.secrets['AZURE_STORAGE_CONNECTION_STRING']
        except:
            pass

    return _CONN_STRING


def _use_azure() -> bool:
    """Check if Azure should be used."""
    if os.getenv('FORCE_LOCAL_DATA', '').lower() in ('true', '1', 'yes'):
        return False
    return bool(_get_connection_string()) and AZURE_AVAILABLE


def _is_headless() -> bool:
    """Check if running in headless environment (GitHub Actions, Streamlit Cloud)."""
    if os.path.exists('/mount/src'):  # Streamlit Cloud
        return True
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        return True
    if os.getenv('STREAMLIT_SERVER_HEADLESS'):
        return True
    return False


def get_blob_service() -> Optional['BlobServiceClient']:
    """Get Azure Blob Service client."""
    if not AZURE_AVAILABLE:
        return None

    conn_str = _get_connection_string()
    if conn_str:
        return BlobServiceClient.from_connection_string(conn_str)

    return None


def get_container_client(create_if_missing: bool = True):
    """Get container client."""
    blob_service = get_blob_service()
    if not blob_service:
        return None

    container = blob_service.get_container_client(CONTAINER_NAME)

    if create_if_missing:
        try:
            if not container.exists():
                container.create_container()
                print(f"Created container: {CONTAINER_NAME}")
        except Exception as e:
            print(f"Note: Could not create container: {e}")

    return container


# =============================================================================
# DATA OPERATIONS
# =============================================================================

def download_parquet(blob_path: str) -> Optional[pd.DataFrame]:
    """Download a parquet file from Azure."""
    from io import BytesIO

    container = get_container_client()
    if not container:
        return None

    try:
        blob_client = container.get_blob_client(blob_path)
        if not blob_client.exists():
            print(f"Blob not found: {blob_path}")
            return None

        data = blob_client.download_blob().readall()
        return pd.read_parquet(BytesIO(data))
    except Exception as e:
        print(f"Error downloading {blob_path}: {e}")
        return None


def _clean_dataframe_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DataFrame for Parquet compatibility."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('').astype(str)
            df[col] = df[col].replace('nan', '')
    return df


def upload_parquet(df: pd.DataFrame, blob_path: str, overwrite: bool = True) -> bool:
    """Upload DataFrame as parquet to Azure."""
    from io import BytesIO

    container = get_container_client()
    if not container:
        print("No Azure connection available")
        return False

    try:
        # Clean data
        df = _clean_dataframe_for_parquet(df)

        buffer = BytesIO()
        df.to_parquet(buffer, index=False, compression='gzip')
        buffer.seek(0)

        file_size_mb = buffer.getbuffer().nbytes / (1024 * 1024)
        print(f"Uploading {len(df):,} rows ({file_size_mb:.1f} MB) to {blob_path}...")

        blob_client = container.get_blob_client(blob_path)
        blob_client.upload_blob(
            buffer,
            overwrite=overwrite,
            max_concurrency=4,
            timeout=600
        )
        print(f"Uploaded successfully: {blob_path}")
        return True
    except Exception as e:
        print(f"Error uploading: {e}")
        return False


def create_backup(blob_path: str) -> Optional[str]:
    """Create backup of a blob file."""
    container = get_container_client()
    if not container:
        return None

    try:
        blob_client = container.get_blob_client(blob_path)
        if not blob_client.exists():
            print(f"No file to backup: {blob_path}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backups/{Path(blob_path).stem}_backup_{timestamp}.parquet"

        backup_client = container.get_blob_client(backup_path)
        backup_client.start_copy_from_url(blob_client.url)

        print(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Backup error: {e}")
        return None


# =============================================================================
# HIGH-LEVEL DATA LOADING
# =============================================================================

def load_rankings() -> pd.DataFrame:
    """Load world rankings from Azure (or local fallback)."""
    if _use_azure():
        print("Loading rankings from Azure Blob Storage...")
        df = download_parquet(BLOB_PATHS['rankings'])
        if df is not None and not df.empty:
            print(f"Loaded {len(df):,} ranking records from Azure")
            return df
        print("Azure empty or unavailable, falling back to local...")

    return _load_local_rankings()


def load_matches() -> pd.DataFrame:
    """Load match data from Azure (or local fallback)."""
    if _use_azure():
        print("Loading matches from Azure Blob Storage...")
        df = download_parquet(BLOB_PATHS['matches'])
        if df is not None and not df.empty:
            print(f"Loaded {len(df):,} match records from Azure")
            return df

    return _load_local_matches()


def load_athletes() -> pd.DataFrame:
    """Load athlete data from Azure (or local fallback)."""
    if _use_azure():
        df = download_parquet(BLOB_PATHS['athletes'])
        if df is not None and not df.empty:
            return df

    return _load_local_athletes()


def _load_local_rankings() -> pd.DataFrame:
    """Load rankings from local CSV files."""
    rankings_dir = Path('data/rankings')
    if not rankings_dir.exists():
        rankings_dir = Path('data_all_categories/rankings')

    csv_files = sorted(rankings_dir.glob('*.csv')) if rankings_dir.exists() else []

    if csv_files:
        try:
            df = pd.read_csv(csv_files[-1], low_memory=False)  # Most recent
            print(f"Loaded {len(df):,} rows from {csv_files[-1].name}")
            return df
        except Exception as e:
            print(f"Error loading local rankings: {e}")

    return pd.DataFrame()


def _load_local_matches() -> pd.DataFrame:
    """Load matches from local CSV files."""
    matches_dir = Path('data/matches')
    all_dfs = []

    if matches_dir.exists():
        for f in matches_dir.glob('*.csv'):
            try:
                df = pd.read_csv(f, low_memory=False)
                if not df.empty:
                    df['source_file'] = f.name
                    all_dfs.append(df)
            except:
                continue

    # Also check data_wt_detailed
    wt_dir = Path('data_wt_detailed')
    if wt_dir.exists():
        for f in wt_dir.glob('*_results_table_0.csv'):
            try:
                df = pd.read_csv(f, low_memory=False)
                if not df.empty:
                    df['source_file'] = f.name
                    all_dfs.append(df)
            except:
                continue

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        print(f"Loaded {len(combined):,} match rows from {len(all_dfs)} files")
        return combined

    return pd.DataFrame()


def _load_local_athletes() -> pd.DataFrame:
    """Load athletes from local CSV files."""
    athletes_dir = Path('data/athletes')
    if athletes_dir.exists():
        csv_files = list(athletes_dir.glob('*.csv'))
        if csv_files:
            try:
                return pd.read_csv(csv_files[0], low_memory=False)
            except:
                pass
    return pd.DataFrame()


def save_rankings(df: pd.DataFrame, create_history: bool = True) -> bool:
    """Save rankings to Azure with optional history snapshot."""
    if not _use_azure():
        print("Azure not configured, saving locally")
        df.to_parquet('data/rankings/world_rankings_latest.parquet', index=False)
        return True

    # Create backup/history
    if create_history:
        timestamp = datetime.now().strftime("%Y%m%d")
        history_path = f"{BLOB_PATHS['rankings_history']}rankings_{timestamp}.parquet"
        upload_parquet(df, history_path)

    # Upload as latest
    return upload_parquet(df, BLOB_PATHS['rankings'])


def save_matches(df: pd.DataFrame, append: bool = True) -> bool:
    """Save matches to Azure."""
    if not _use_azure():
        print("Azure not configured, saving locally")
        df.to_parquet('data/matches/matches_master.parquet', index=False)
        return True

    if append:
        existing = download_parquet(BLOB_PATHS['matches'])
        if existing is not None and not existing.empty:
            df = pd.concat([existing, df], ignore_index=True)
            # Remove duplicates if we have an ID column
            if 'match_id' in df.columns:
                df = df.drop_duplicates(subset=['match_id'], keep='last')

    return upload_parquet(df, BLOB_PATHS['matches'])


# =============================================================================
# MIGRATION UTILITIES
# =============================================================================

def migrate_local_to_azure() -> Dict[str, bool]:
    """Migrate all local data to Azure Blob Storage."""
    print("=" * 60)
    print("MIGRATING LOCAL DATA TO AZURE BLOB STORAGE")
    print("=" * 60)

    results = {}

    # Migrate rankings
    rankings_df = _load_local_rankings()
    if not rankings_df.empty:
        results['rankings'] = save_rankings(rankings_df, create_history=True)
        print(f"Rankings: {len(rankings_df):,} rows - {'OK' if results['rankings'] else 'FAILED'}")

    # Migrate matches
    matches_df = _load_local_matches()
    if not matches_df.empty:
        results['matches'] = upload_parquet(matches_df, BLOB_PATHS['matches'])
        print(f"Matches: {len(matches_df):,} rows - {'OK' if results['matches'] else 'FAILED'}")

    # Migrate athletes
    athletes_df = _load_local_athletes()
    if not athletes_df.empty:
        results['athletes'] = upload_parquet(athletes_df, BLOB_PATHS['athletes'])
        print(f"Athletes: {len(athletes_df):,} rows - {'OK' if results['athletes'] else 'FAILED'}")

    print("=" * 60)
    print("Migration complete!")
    return results


def get_storage_usage() -> dict:
    """Get storage usage statistics."""
    container = get_container_client()
    if not container:
        return {'error': 'Not connected to Azure'}

    total_size = 0
    files = []

    try:
        for blob in container.list_blobs():
            size_mb = blob.size / (1024 * 1024)
            total_size += blob.size
            files.append({'name': blob.name, 'size_mb': round(size_mb, 2)})
    except Exception as e:
        return {'error': str(e)}

    return {
        'total_mb': round(total_size / (1024 * 1024), 2),
        'total_gb': round(total_size / (1024 * 1024 * 1024), 3),
        'free_tier_limit_gb': 5,
        'percent_used': round((total_size / (5 * 1024 * 1024 * 1024)) * 100, 1),
        'files': sorted(files, key=lambda x: x['size_mb'], reverse=True)
    }


# =============================================================================
# DUCKDB QUERY SUPPORT
# =============================================================================

_duckdb_conn = None
_duckdb_tables = {}


def get_duckdb_connection():
    """Get DuckDB connection with data loaded."""
    global _duckdb_conn, _duckdb_tables

    if not DUCKDB_AVAILABLE:
        print("DuckDB not available")
        return None

    if _duckdb_conn is not None:
        return _duckdb_conn

    try:
        _duckdb_conn = duckdb.connect(':memory:')
        print("Initializing DuckDB...")

        # Load rankings
        rankings_df = load_rankings()
        if not rankings_df.empty:
            _duckdb_conn.register('rankings', rankings_df)
            _duckdb_tables['rankings'] = len(rankings_df)
            print(f"  - rankings: {len(rankings_df):,} rows")

        # Load matches
        matches_df = load_matches()
        if not matches_df.empty:
            _duckdb_conn.register('matches', matches_df)
            _duckdb_tables['matches'] = len(matches_df)
            print(f"  - matches: {len(matches_df):,} rows")

        # Load athletes
        athletes_df = load_athletes()
        if not athletes_df.empty:
            _duckdb_conn.register('athletes', athletes_df)
            _duckdb_tables['athletes'] = len(athletes_df)
            print(f"  - athletes: {len(athletes_df):,} rows")

        print("DuckDB ready!")
        return _duckdb_conn

    except Exception as e:
        print(f"DuckDB initialization error: {e}")
        return None


def query(sql: str) -> Optional[pd.DataFrame]:
    """Execute SQL query against loaded data.

    Available tables:
        - rankings: World rankings data
        - matches: Match/bout results
        - athletes: Athlete profiles

    Examples:
        query("SELECT * FROM rankings WHERE country = 'KSA' ORDER BY rank")
        query("SELECT weight_category, COUNT(*) FROM rankings GROUP BY weight_category")
        query("SELECT * FROM matches WHERE winner_name LIKE '%Saudi%'")
    """
    conn = get_duckdb_connection()
    if conn is None:
        return None

    try:
        return conn.execute(sql).fetchdf()
    except Exception as e:
        print(f"Query error: {e}")
        return None


def refresh_data():
    """Reload all data from Azure into DuckDB."""
    global _duckdb_conn, _duckdb_tables

    if _duckdb_conn is not None:
        _duckdb_conn.close()
    _duckdb_conn = None
    _duckdb_tables = {}

    return get_duckdb_connection()


def get_saudi_rankings() -> pd.DataFrame:
    """Convenience function: Get Saudi athlete rankings."""
    return query("""
        SELECT * FROM rankings
        WHERE UPPER(country) LIKE '%KSA%'
           OR UPPER(country) LIKE '%SAUDI%'
        ORDER BY rank
    """) or pd.DataFrame()


def get_saudi_matches() -> pd.DataFrame:
    """Convenience function: Get matches involving Saudi athletes."""
    return query("""
        SELECT * FROM matches
        WHERE UPPER(athlete1_country) LIKE '%KSA%'
           OR UPPER(athlete2_country) LIKE '%KSA%'
           OR UPPER(athlete1_name) LIKE '%SAUDI%'
           OR UPPER(athlete2_name) LIKE '%SAUDI%'
        ORDER BY date DESC
    """) or pd.DataFrame()


# =============================================================================
# TEST CONNECTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TAEKWONDO AZURE BLOB STORAGE CONNECTION TEST")
    print("=" * 60)

    if _use_azure():
        print(f"\nContainer: {CONTAINER_NAME}")
        print(f"Storage URL: {STORAGE_ACCOUNT_URL}")
        print(f"Headless mode: {_is_headless()}")

        usage = get_storage_usage()
        if 'error' not in usage:
            print(f"\nStorage Usage: {usage['total_mb']:.2f} MB ({usage['percent_used']:.1f}% of 5 GB free tier)")
            print(f"\nFiles in container:")
            for f in usage['files'][:10]:
                print(f"  - {f['name']}: {f['size_mb']} MB")
            if len(usage['files']) > 10:
                print(f"  ... and {len(usage['files']) - 10} more files")
            print("\nConnection: SUCCESS")
        else:
            print(f"\nConnection: FAILED - {usage['error']}")
    else:
        print("\nAzure not configured.")
        print("Set AZURE_STORAGE_CONNECTION_STRING in .env file")
        print("\nFalling back to local data...")

    # Test data loading
    print("\n" + "-" * 60)
    print("DATA LOADING TEST")
    print("-" * 60)

    rankings = load_rankings()
    print(f"Rankings loaded: {len(rankings):,} rows")

    matches = load_matches()
    print(f"Matches loaded: {len(matches):,} rows")

    # Test DuckDB
    if DUCKDB_AVAILABLE:
        print("\n" + "-" * 60)
        print("DUCKDB QUERY TEST")
        print("-" * 60)

        saudi = get_saudi_rankings()
        print(f"Saudi athletes in rankings: {len(saudi)}")
        if not saudi.empty:
            print(saudi.head())

    print("\n" + "=" * 60)
