"""
Manual Rankings Import Tool
============================

When automated scraping is blocked by CloudFlare, use this tool to manually
import rankings data from CSV files exported from the World Taekwondo website.

Instructions:
1. Go to https://www.worldtaekwondo.org/athletes/Ranking/contents
2. For each weight category, use browser's "Copy Table" or save as CSV
3. Save files in data/imports/ folder with naming: {category}_import.csv
4. Run this script to process and merge all imports

Usage:
    python import_rankings_manual.py [--source data/imports]
"""

import sys
import io

try:
    if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (ValueError, AttributeError):
    pass

import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import json
import re


# Weight category mapping for validation
WEIGHT_CATEGORIES = {
    'M-54kg', 'M-58kg', 'M-63kg', 'M-68kg', 'M-74kg', 'M-80kg', 'M-87kg', 'M+87kg',
    'F-46kg', 'F-49kg', 'F-53kg', 'F-57kg', 'F-62kg', 'F-67kg', 'F-73kg', 'F+73kg',
}


def detect_weight_category(filename: str, df: pd.DataFrame) -> str:
    """Detect weight category from filename or data"""
    # Try to extract from filename
    filename_lower = filename.lower()

    for cat in WEIGHT_CATEGORIES:
        cat_lower = cat.lower().replace('+', 'plus').replace('-', '')
        if cat_lower in filename_lower.replace('-', '').replace('_', '').replace('+', 'plus'):
            return cat

    # Check if weight category column exists
    if 'weight_category' in df.columns:
        categories = df['weight_category'].dropna().unique()
        if len(categories) == 1:
            return categories[0]

    # Ask user
    print(f"\nCould not detect weight category for: {filename}")
    print("Available categories:")
    for i, cat in enumerate(sorted(WEIGHT_CATEGORIES)):
        print(f"  {i+1}. {cat}")

    while True:
        choice = input("Enter category number or name: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(WEIGHT_CATEGORIES):
            return sorted(WEIGHT_CATEGORIES)[int(choice)-1]
        if choice in WEIGHT_CATEGORIES:
            return choice
        print("Invalid choice. Try again.")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names"""
    # Common column name mappings
    column_mappings = {
        'RANK': 'rank',
        'Rank': 'rank',
        '↑↓': 'rank_change',
        'NAME': 'athlete_name',
        'Name': 'athlete_name',
        'MEMBER NATION': 'country',
        'Member Nation': 'country',
        'Country': 'country',
        'POINTS': 'points',
        'Points': 'points',
    }

    df = df.rename(columns=column_mappings)
    return df


def process_import_file(filepath: Path, output_dir: Path) -> pd.DataFrame:
    """Process a single import file"""
    print(f"\nProcessing: {filepath.name}")

    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except:
                continue
        else:
            print(f"  [ERROR] Could not read file with any encoding")
            return pd.DataFrame()

        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")

        # Standardize columns
        df = standardize_columns(df)

        # Detect weight category
        weight_category = detect_weight_category(filepath.name, df)
        print(f"  Category: {weight_category}")

        # Add metadata
        df['weight_category'] = weight_category
        df['gender'] = weight_category[0]  # M or F
        df['imported_at'] = datetime.now().isoformat()
        df['source_file'] = filepath.name

        # Clean data
        if 'rank' in df.columns:
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
            df = df[df['rank'].notna()]
            df['rank'] = df['rank'].astype(int)

        if 'points' in df.columns:
            df['points'] = pd.to_numeric(df['points'], errors='coerce')

        # Remove duplicates
        if 'athlete_name' in df.columns:
            df = df.drop_duplicates(subset=['athlete_name', 'weight_category'], keep='first')

        print(f"  Processed: {len(df)} athletes")
        return df

    except Exception as e:
        print(f"  [ERROR] {e}")
        return pd.DataFrame()


def merge_rankings(dfs: list, output_dir: Path) -> pd.DataFrame:
    """Merge all processed rankings"""
    if not dfs:
        return pd.DataFrame()

    # Combine all dataframes
    combined = pd.concat(dfs, ignore_index=True)

    # Sort by weight category and rank
    combined = combined.sort_values(['weight_category', 'rank'])

    return combined


def save_results(df: pd.DataFrame, output_dir: Path):
    """Save processed rankings"""
    if df.empty:
        print("\n[WARN] No data to save")
        return

    timestamp = datetime.now().strftime('%Y%m%d')
    rankings_dir = output_dir / 'rankings'
    athletes_dir = output_dir / 'athletes'
    rankings_dir.mkdir(parents=True, exist_ok=True)
    athletes_dir.mkdir(parents=True, exist_ok=True)

    # Save combined file
    combined_path = rankings_dir / f'world_rankings_all_{timestamp}.csv'
    df.to_csv(combined_path, index=False, encoding='utf-8-sig')
    print(f"\n[SAVED] Combined: {combined_path}")

    # Save as latest
    latest_path = rankings_dir / 'world_rankings_latest.csv'
    df.to_csv(latest_path, index=False, encoding='utf-8-sig')
    print(f"[SAVED] Latest: {latest_path}")

    # Save by category
    for cat in df['weight_category'].unique():
        cat_df = df[df['weight_category'] == cat]
        cat_path = rankings_dir / f'{cat}_rankings_{timestamp}.csv'
        cat_df.to_csv(cat_path, index=False, encoding='utf-8-sig')
        print(f"[SAVED] {cat}: {len(cat_df)} athletes")

    # Save athletes file
    athletes_cols = ['rank', 'athlete_name', 'country', 'points', 'weight_category', 'gender']
    available_cols = [c for c in athletes_cols if c in df.columns]
    athletes_df = df[available_cols].copy()

    if 'athlete_name' in athletes_df.columns:
        athletes_df = athletes_df.rename(columns={'athlete_name': 'name'})

    athletes_df['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    athletes_path = athletes_dir / 'athletes_from_rankings.csv'
    athletes_df.to_csv(athletes_path, index=False, encoding='utf-8-sig')
    print(f"[SAVED] Athletes: {athletes_path}")

    # Summary
    print(f"\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Total athletes: {len(df)}")
    print(f"Categories: {df['weight_category'].nunique()}")
    print(f"Countries: {df['country'].nunique()}")

    # Check for Saudi athletes
    country_col = 'country' if 'country' in df.columns else None
    if country_col:
        saudi_df = df[df[country_col].str.upper().str.contains('KSA|SAUDI', na=False)]
        if not saudi_df.empty:
            print(f"\nSaudi Athletes ({len(saudi_df)}):")
            for _, row in saudi_df.iterrows():
                name = row.get('athlete_name', row.get('name', 'Unknown'))
                cat = row.get('weight_category', 'Unknown')
                rank = row.get('rank', '?')
                print(f"  - {name} ({cat}): #{rank}")

            # Save Saudi athletes
            saudi_path = athletes_dir / 'saudi_athletes.csv'
            saudi_df.to_csv(saudi_path, index=False, encoding='utf-8-sig')
            print(f"\n[SAVED] Saudi athletes: {saudi_path}")


def create_sample_import():
    """Create a sample import file for reference"""
    sample_data = """rank,rank_change,athlete_name,country,points
1,-,Mohamed Khalil JENDOUBI (TUN-1731),Tunisia,230.4
2,-,Eunsu SEO (KOR-10704),Republic of Korea,198.6
3,-,ARISTEIDIS NIKOLAOS PSARROS (GRE-5679),Greece,194.72
4,-,Abolfazl ZANDI (IRI-21260),Islamic Republic Of Iran,190.8
5,-,Tae-Joon PARK (KOR-5579),Republic of Korea,150.22"""

    import_dir = Path('data/imports')
    import_dir.mkdir(parents=True, exist_ok=True)

    sample_path = import_dir / 'M-58kg_sample.csv'
    with open(sample_path, 'w', encoding='utf-8') as f:
        f.write(sample_data)

    print(f"\nSample import file created: {sample_path}")
    print("Edit this file or add your own CSV files to data/imports/")


def main():
    parser = argparse.ArgumentParser(description='Import rankings data manually')
    parser.add_argument('--source', '-s', default='data/imports', help='Source directory with CSV files')
    parser.add_argument('--output', '-o', default='data', help='Output directory')
    parser.add_argument('--create-sample', action='store_true', help='Create a sample import file')

    args = parser.parse_args()

    print("="*60)
    print("MANUAL RANKINGS IMPORT TOOL")
    print("="*60)
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")

    if args.create_sample:
        create_sample_import()
        return

    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        print(f"\n[ERROR] Source directory not found: {source_dir}")
        print("Create the directory and add CSV files, or use --create-sample")
        source_dir.mkdir(parents=True, exist_ok=True)
        create_sample_import()
        return

    # Find CSV files
    csv_files = list(source_dir.glob('*.csv'))

    if not csv_files:
        print(f"\n[ERROR] No CSV files found in {source_dir}")
        print("Add CSV files or use --create-sample")
        create_sample_import()
        return

    print(f"\nFound {len(csv_files)} CSV file(s)")

    # Process each file
    processed_dfs = []
    for csv_file in csv_files:
        df = process_import_file(csv_file, output_dir)
        if not df.empty:
            processed_dfs.append(df)

    # Merge and save
    if processed_dfs:
        combined = merge_rankings(processed_dfs, output_dir)
        save_results(combined, output_dir)
    else:
        print("\n[ERROR] No data could be processed")


if __name__ == '__main__':
    main()
