"""
Data Export Utilities - CSV to Parquet conversion for Azure
Parquet files are smaller and faster for DuckDB/Azure analytics
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    print("[WARN] PyArrow not installed. Run: pip install pyarrow")


def csv_to_parquet(csv_path: Path, parquet_path: Path = None) -> Path:
    """Convert CSV file to Parquet format"""
    if not PARQUET_AVAILABLE:
        print("[ERROR] PyArrow required for Parquet export")
        return None

    df = pd.read_csv(csv_path)

    if parquet_path is None:
        parquet_path = csv_path.with_suffix('.parquet')

    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')

    csv_size = csv_path.stat().st_size
    parquet_size = parquet_path.stat().st_size
    reduction = (1 - parquet_size / csv_size) * 100

    print(f"[OK] {csv_path.name} -> {parquet_path.name}")
    print(f"     CSV: {csv_size:,} bytes | Parquet: {parquet_size:,} bytes ({reduction:.1f}% smaller)")

    return parquet_path


def convert_all_csv_to_parquet(data_dir: str = "data") -> dict:
    """Convert all CSV files in data directory to Parquet"""
    data_path = Path(data_dir)
    results = {
        'converted': [],
        'failed': [],
        'total_csv_size': 0,
        'total_parquet_size': 0,
    }

    csv_files = list(data_path.glob('**/*.csv'))
    print(f"\n[INFO] Found {len(csv_files)} CSV files to convert")

    for csv_file in csv_files:
        try:
            parquet_file = csv_to_parquet(csv_file)
            if parquet_file:
                results['converted'].append(str(csv_file))
                results['total_csv_size'] += csv_file.stat().st_size
                results['total_parquet_size'] += parquet_file.stat().st_size
        except Exception as e:
            print(f"[ERROR] {csv_file}: {e}")
            results['failed'].append(str(csv_file))

    if results['total_csv_size'] > 0:
        reduction = (1 - results['total_parquet_size'] / results['total_csv_size']) * 100
        print(f"\n[SUMMARY]")
        print(f"  Converted: {len(results['converted'])} files")
        print(f"  Total CSV: {results['total_csv_size']:,} bytes")
        print(f"  Total Parquet: {results['total_parquet_size']:,} bytes")
        print(f"  Size reduction: {reduction:.1f}%")

    return results


def upload_parquet_to_azure(container_name: str = 'taekwondo-data'):
    """Upload all Parquet files to Azure Blob Storage"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("[ERROR] No Azure connection string in .env")
        return False

    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("[ERROR] azure-storage-blob required. Run: pip install azure-storage-blob")
        return False

    blob_service = BlobServiceClient.from_connection_string(connection_string)
    container = blob_service.get_container_client(container_name)

    # Ensure container exists
    try:
        container.create_container()
        print(f"[OK] Created container: {container_name}")
    except Exception as e:
        if 'ContainerAlreadyExists' not in str(e):
            print(f"[WARN] Container: {e}")

    # Upload all Parquet files
    data_path = Path('data')
    parquet_files = list(data_path.glob('**/*.parquet'))

    print(f"\n[INFO] Uploading {len(parquet_files)} Parquet files to Azure...")

    uploaded = 0
    for pq_file in parquet_files:
        blob_name = f"parquet/{pq_file.parent.name}/{pq_file.name}"
        try:
            with open(pq_file, 'rb') as data:
                container.upload_blob(name=blob_name, data=data, overwrite=True)
            print(f"  [OK] {blob_name}")
            uploaded += 1
        except Exception as e:
            print(f"  [ERROR] {blob_name}: {e}")

    print(f"\n[SUMMARY] Uploaded {uploaded}/{len(parquet_files)} files to Azure")
    return uploaded > 0


def create_duckdb_database(db_path: str = "data/taekwondo.duckdb"):
    """Create DuckDB database from Parquet files for fast analytics"""
    try:
        import duckdb
    except ImportError:
        print("[ERROR] DuckDB required. Run: pip install duckdb")
        return None

    conn = duckdb.connect(db_path)

    # Create tables from Parquet files
    parquet_mappings = {
        'rankings': 'data/profiles/all_rankings_latest.parquet',
        'top20': 'data/profiles/top20_global.parquet',
        'asian_rivals': 'data/profiles/asian_rivals.parquet',
        'priority_athletes': 'data/profiles/priority_athletes_latest.parquet',
    }

    for table_name, parquet_path in parquet_mappings.items():
        if Path(parquet_path).exists():
            conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"[OK] Created table '{table_name}' with {count} rows")
        else:
            print(f"[SKIP] {parquet_path} not found")

    # Create useful views
    conn.execute("""
        CREATE OR REPLACE VIEW saudi_athletes AS
        SELECT * FROM rankings
        WHERE country LIKE '%Saudi%' OR country LIKE '%KSA%'
    """)

    conn.execute("""
        CREATE OR REPLACE VIEW medal_contenders AS
        SELECT * FROM rankings
        WHERE rank <= 20 AND is_asian_rival = true
        ORDER BY weight_category, rank
    """)

    print(f"\n[OK] DuckDB database created: {db_path}")
    print("     Use: duckdb data/taekwondo.duckdb")
    print("     Query: SELECT * FROM rankings WHERE country LIKE '%Korea%'")

    conn.close()
    return db_path


def main():
    """Main export utility"""
    print("="*60)
    print("DATA EXPORT UTILITY")
    print("="*60)

    # Step 1: Convert CSV to Parquet
    print("\n[STEP 1] Converting CSV to Parquet...")
    convert_all_csv_to_parquet('data')

    # Step 2: Create DuckDB database
    print("\n[STEP 2] Creating DuckDB database...")
    create_duckdb_database()

    # Step 3: Upload to Azure (optional)
    print("\n[STEP 3] Upload to Azure? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        upload_parquet_to_azure()

    print("\n[DONE] Data export complete!")


if __name__ == '__main__':
    main()
