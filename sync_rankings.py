"""
Taekwondo Rankings Sync Script for GitHub Actions
Scrapes World Taekwondo rankings and uploads to Azure Blob Storage

Usage:
    python sync_rankings.py                    # Full sync
    python sync_rankings.py --check-only       # Just check for changes
    python sync_rankings.py --migrate          # Migrate local data to Azure

GitHub Actions Environment Variables Required:
    AZURE_STORAGE_CONNECTION_STRING - Azure Blob connection string
    SENDGRID_API_KEY - For email alerts (optional)
    SLACK_WEBHOOK_URL - For Slack alerts (optional)
"""

import os
import sys
import io
import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# UTF-8 encoding for Windows/Linux compatibility
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

# Local imports
try:
    from blob_storage import (
        load_rankings, save_rankings, upload_parquet,
        download_parquet, get_storage_usage, _use_azure,
        BLOB_PATHS
    )
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    BLOB_STORAGE_AVAILABLE = False
    print("Warning: blob_storage module not found")

try:
    from scraper_agent_incremental import IncrementalScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    print("Warning: scraper_agent_incremental not found, using fallback")


# =============================================================================
# CONFIGURATION
# =============================================================================

CHANGE_HISTORY_FILE = 'ranking_changes.json'
ALERT_THRESHOLDS = {
    'ksa_rank_drop': 3,        # Alert if KSA athlete drops 3+ positions
    'ksa_rank_improve': 1,     # Alert on any improvement
    'rival_overtake': True,    # Alert if rival passes KSA athlete
}

RIVAL_COUNTRIES = ['KOR', 'IRI', 'JOR', 'TUR', 'CHN', 'GBR', 'FRA', 'MEX', 'UAE', 'THA']
ASIAN_RIVALS = ['KOR', 'IRI', 'JOR', 'CHN', 'JPN', 'UZB', 'THA', 'KAZ']


# =============================================================================
# SCRAPING FUNCTIONS
# =============================================================================

def scrape_rankings() -> pd.DataFrame:
    """Scrape current world rankings from World Taekwondo."""
    print("Scraping World Taekwondo rankings...")

    if SCRAPER_AVAILABLE:
        try:
            scraper = IncrementalScraper()
            scraper.scrape_category('rankings')

            # Load the scraped data
            rankings_dir = Path('data_incremental/rankings')
            if rankings_dir.exists():
                csv_files = sorted(rankings_dir.glob('*.csv'))
                if csv_files:
                    df = pd.read_csv(csv_files[-1])
                    print(f"Scraped {len(df):,} ranking records")
                    return df
        except Exception as e:
            print(f"Incremental scraper error: {e}")

    # Fallback: try existing local data
    print("Using fallback: loading existing local data...")
    return _load_local_rankings_fallback()


def _load_local_rankings_fallback() -> pd.DataFrame:
    """Fallback to load local ranking files."""
    for data_dir in ['data_incremental/rankings', 'data_all_categories/rankings', 'data/rankings']:
        path = Path(data_dir)
        if path.exists():
            csv_files = sorted(path.glob('*.csv'))
            if csv_files:
                try:
                    df = pd.read_csv(csv_files[-1])
                    print(f"Loaded {len(df):,} rows from {csv_files[-1]}")
                    return df
                except Exception as e:
                    print(f"Error loading {csv_files[-1]}: {e}")

    return pd.DataFrame()


# =============================================================================
# CHANGE DETECTION
# =============================================================================

def compute_data_hash(df: pd.DataFrame) -> str:
    """Compute hash of DataFrame for change detection."""
    if df.empty:
        return ""

    # Sort to ensure consistent hash
    df_sorted = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    return hashlib.md5(df_sorted.to_json().encode()).hexdigest()


def detect_ranking_changes(old_df: pd.DataFrame, new_df: pd.DataFrame) -> Dict:
    """Detect significant ranking changes between two snapshots."""
    changes = {
        'timestamp': datetime.now().isoformat(),
        'ksa_improvements': [],
        'ksa_drops': [],
        'rival_overtakes': [],
        'new_entries': [],
        'dropped_out': [],
        'summary': {}
    }

    if old_df.empty or new_df.empty:
        changes['summary']['status'] = 'insufficient_data'
        return changes

    # Normalize column names
    old_df = _normalize_columns(old_df.copy())
    new_df = _normalize_columns(new_df.copy())

    # Get Saudi athletes
    old_saudi = old_df[old_df['country'].str.upper().str.contains('KSA|SAUDI', na=False)]
    new_saudi = new_df[new_df['country'].str.upper().str.contains('KSA|SAUDI', na=False)]

    # Check each Saudi athlete
    for _, new_row in new_saudi.iterrows():
        athlete_name = new_row.get('athlete_name', '')
        new_rank = pd.to_numeric(new_row.get('rank'), errors='coerce')

        if pd.isna(new_rank):
            continue

        # Find in old data
        old_match = old_saudi[old_saudi['athlete_name'] == athlete_name]

        if old_match.empty:
            changes['new_entries'].append({
                'athlete': athlete_name,
                'category': new_row.get('weight_category', ''),
                'new_rank': int(new_rank)
            })
        else:
            old_rank = pd.to_numeric(old_match.iloc[0].get('rank'), errors='coerce')
            if pd.notna(old_rank):
                rank_change = int(old_rank - new_rank)  # Positive = improvement

                if rank_change > 0:  # Improved
                    changes['ksa_improvements'].append({
                        'athlete': athlete_name,
                        'category': new_row.get('weight_category', ''),
                        'old_rank': int(old_rank),
                        'new_rank': int(new_rank),
                        'change': rank_change
                    })
                elif rank_change < -ALERT_THRESHOLDS['ksa_rank_drop']:  # Dropped significantly
                    changes['ksa_drops'].append({
                        'athlete': athlete_name,
                        'category': new_row.get('weight_category', ''),
                        'old_rank': int(old_rank),
                        'new_rank': int(new_rank),
                        'change': rank_change
                    })

    # Check for dropped athletes
    for _, old_row in old_saudi.iterrows():
        athlete_name = old_row.get('athlete_name', '')
        if athlete_name not in new_saudi['athlete_name'].values:
            changes['dropped_out'].append({
                'athlete': athlete_name,
                'category': old_row.get('weight_category', ''),
                'last_rank': int(pd.to_numeric(old_row.get('rank'), errors='coerce') or 0)
            })

    # Summary
    changes['summary'] = {
        'total_ksa_athletes': len(new_saudi),
        'improvements': len(changes['ksa_improvements']),
        'drops': len(changes['ksa_drops']),
        'new_entries': len(changes['new_entries']),
        'dropped_out': len(changes['dropped_out']),
        'has_significant_changes': (
            len(changes['ksa_improvements']) > 0 or
            len(changes['ksa_drops']) > 0 or
            len(changes['new_entries']) > 0
        )
    }

    return changes


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for consistency."""
    column_map = {
        'RANK': 'rank',
        'MEMBER NATION': 'country',
        'NAME': 'athlete_name',
        'WEIGHT CATEGORY': 'weight_category',
        'POINTS': 'points'
    }

    for old_name, new_name in column_map.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})

    return df


# =============================================================================
# SYNC WORKFLOW
# =============================================================================

def sync_rankings(check_only: bool = False) -> Dict:
    """Main sync workflow: scrape, compare, upload, alert."""
    print("=" * 60)
    print("TAEKWONDO RANKINGS SYNC")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    result = {
        'success': False,
        'timestamp': datetime.now().isoformat(),
        'records_scraped': 0,
        'changes': None,
        'uploaded': False,
        'alerts_sent': False,
        'error': None
    }

    try:
        # Step 1: Load previous data from Azure
        print("\n[1/4] Loading previous rankings from Azure...")
        old_rankings = load_rankings() if BLOB_STORAGE_AVAILABLE else pd.DataFrame()
        print(f"Previous records: {len(old_rankings):,}")

        # Step 2: Scrape new rankings
        print("\n[2/4] Scraping current rankings...")
        new_rankings = scrape_rankings()
        result['records_scraped'] = len(new_rankings)
        print(f"New records: {len(new_rankings):,}")

        if new_rankings.empty:
            result['error'] = "No data scraped"
            print("ERROR: No data scraped!")
            return result

        # Step 3: Detect changes
        print("\n[3/4] Detecting changes...")
        changes = detect_ranking_changes(old_rankings, new_rankings)
        result['changes'] = changes

        print(f"  KSA Improvements: {changes['summary'].get('improvements', 0)}")
        print(f"  KSA Drops: {changes['summary'].get('drops', 0)}")
        print(f"  New Entries: {changes['summary'].get('new_entries', 0)}")

        if check_only:
            print("\n[CHECK ONLY MODE - not uploading]")
            result['success'] = True
            return result

        # Step 4: Upload to Azure
        print("\n[4/4] Uploading to Azure Blob Storage...")
        if BLOB_STORAGE_AVAILABLE and _use_azure():
            result['uploaded'] = save_rankings(new_rankings, create_history=True)
            print(f"Upload: {'SUCCESS' if result['uploaded'] else 'FAILED'}")
        else:
            print("Azure not configured - saving locally")
            output_dir = Path('data/rankings')
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d')
            new_rankings.to_csv(output_dir / f'rankings_{timestamp}.csv', index=False)
            new_rankings.to_parquet(output_dir / 'world_rankings_latest.parquet', index=False)
            result['uploaded'] = True

        # Save change history
        _save_change_history(changes)

        result['success'] = True
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)

    except Exception as e:
        result['error'] = str(e)
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    return result


def _save_change_history(changes: Dict):
    """Append changes to history file."""
    history_file = Path(CHANGE_HISTORY_FILE)

    history = []
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []

    history.append(changes)

    # Keep last 100 entries
    history = history[-100:]

    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"Change history saved: {history_file}")


# =============================================================================
# ALERT OUTPUT (for GitHub Actions)
# =============================================================================

def generate_alert_output(changes: Dict) -> str:
    """Generate alert message for GitHub Actions output."""
    if not changes or not changes.get('summary', {}).get('has_significant_changes'):
        return ""

    lines = [
        "🥋 TAEKWONDO RANKING ALERT - KSA",
        "",
        f"Sync Time: {changes.get('timestamp', 'Unknown')}",
        ""
    ]

    if changes.get('ksa_improvements'):
        lines.append("✅ IMPROVEMENTS:")
        for imp in changes['ksa_improvements']:
            lines.append(f"  • {imp['athlete']} ({imp['category']}): #{imp['old_rank']} → #{imp['new_rank']} (+{imp['change']})")
        lines.append("")

    if changes.get('ksa_drops'):
        lines.append("⚠️ DROPS:")
        for drop in changes['ksa_drops']:
            lines.append(f"  • {drop['athlete']} ({drop['category']}): #{drop['old_rank']} → #{drop['new_rank']} ({drop['change']})")
        lines.append("")

    if changes.get('new_entries'):
        lines.append("🆕 NEW ENTRIES:")
        for entry in changes['new_entries']:
            lines.append(f"  • {entry['athlete']} ({entry['category']}): #{entry['new_rank']}")
        lines.append("")

    lines.extend([
        "---",
        "Saudi Taekwondo Analytics | Automated Sync"
    ])

    return "\n".join(lines)


def set_github_output(name: str, value: str):
    """Set GitHub Actions output variable."""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
    else:
        print(f"[OUTPUT] {name}={value}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Taekwondo Rankings Sync')
    parser.add_argument('--check-only', action='store_true',
                        help='Check for changes without uploading')
    parser.add_argument('--migrate', action='store_true',
                        help='Migrate local data to Azure')
    parser.add_argument('--storage-info', action='store_true',
                        help='Show Azure storage usage')

    args = parser.parse_args()

    if args.storage_info:
        if BLOB_STORAGE_AVAILABLE:
            usage = get_storage_usage()
            print(json.dumps(usage, indent=2))
        else:
            print("Blob storage module not available")
        return

    if args.migrate:
        if BLOB_STORAGE_AVAILABLE:
            from blob_storage import migrate_local_to_azure
            migrate_local_to_azure()
        else:
            print("Blob storage module not available")
        return

    # Run sync
    result = sync_rankings(check_only=args.check_only)

    # Set GitHub Actions outputs
    set_github_output('success', str(result['success']).lower())
    set_github_output('records', str(result['records_scraped']))
    set_github_output('has_changes', str(
        result.get('changes', {}).get('summary', {}).get('has_significant_changes', False)
    ).lower())

    if result.get('changes'):
        alert_msg = generate_alert_output(result['changes'])
        if alert_msg:
            print("\n" + "-" * 60)
            print("ALERT MESSAGE:")
            print("-" * 60)
            print(alert_msg)

            # Save alert for next workflow step
            with open('alert_message.txt', 'w') as f:
                f.write(alert_msg)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
