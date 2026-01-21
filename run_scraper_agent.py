"""
Master Scraper Agent Runner
Simple interface to run all scraping agents with recommended settings
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import subprocess
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def run_diagnostics():
    """Run diagnostic agent"""
    print_header("RUNNING DIAGNOSTICS")
    print("This will test your scraper setup and identify any issues.")
    print("Browser will be VISIBLE for debugging.\n")

    proceed = input("Continue? (y/n): ").lower()
    if proceed != 'y':
        print("Skipped.")
        return

    subprocess.run([
        sys.executable,
        "scraper_diagnostic_agent.py",
        "--visible"
    ])

    print("\n✓ Diagnostics complete!")
    print("  Check 'scraper_diagnostics/' folder for results")


def run_quick_scrape():
    """Run quick scrape of top priorities"""
    print_header("QUICK SCRAPE (Top 3 Categories)")
    print("This will scrape:")
    print("  1. World Rankings (current)")
    print("  2. Olympic Games Results")
    print("  3. World Championships")
    print("\nEstimated time: 1-2 minutes\n")

    proceed = input("Continue? (y/n): ").lower()
    if proceed != 'y':
        print("Skipped.")
        return

    subprocess.run([
        sys.executable,
        "scraper_agent_complete.py",
        "--max-pages", "3"
    ])

    print("\n✓ Quick scrape complete!")
    print("  Check 'data_scraped/' folder for results")


def run_full_scrape():
    """Run full autonomous scrape"""
    print_header("FULL SCRAPE (All Categories)")
    print("This will scrape all 5 competition categories:")
    print("  1. World Rankings")
    print("  2. Olympic Games")
    print("  3. World Championships")
    print("  4. Grand Prix")
    print("  5. Grand Slam")
    print("\nEstimated time: 3-5 minutes\n")

    proceed = input("Continue? (y/n): ").lower()
    if proceed != 'y':
        print("Skipped.")
        return

    subprocess.run([
        sys.executable,
        "scraper_agent_complete.py"
    ])

    print("\n✓ Full scrape complete!")
    print("  Check 'data_scraped/' folder for results")


def run_download_files():
    """Run file downloader"""
    print_header("DOWNLOAD FILES")
    print("This will download Excel/PDF files from World Taekwondo.")
    print("Files include: Rankings, Results, Competition Data")
    print("\nMax runtime: 8 minutes")
    print("Year range: 2020-present\n")

    proceed = input("Continue? (y/n): ").lower()
    if proceed != 'y':
        print("Skipped.")
        return

    subprocess.run([
        sys.executable,
        "download_all_taekwondo_data_fixed.py"
    ])

    print("\n✓ Download complete!")
    print("  Check 'taekwondo_data/' folder for files")


def view_latest_data():
    """Show latest scraped data"""
    print_header("LATEST DATA")

    data_dir = Path("data_scraped/rankings")
    if not data_dir.exists():
        print("No data found. Run a scrape first.")
        return

    # Find latest CSV
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found.")
        return

    latest = max(csv_files, key=lambda p: p.stat().st_mtime)

    print(f"Latest file: {latest.name}")
    print(f"Modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
    print(f"Size: {latest.stat().st_size:,} bytes")

    print("\nFirst 10 rows:")
    print("-" * 70)

    with open(latest, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            if i >= 11:  # Header + 10 rows
                break
            print(line.rstrip())

    print("-" * 70)


def run_incremental_update():
    """Run smart incremental update"""
    print_header("INCREMENTAL UPDATE (Smart)")
    print("This will:")
    print("  ✓ Only scrape changed data")
    print("  ✓ Check back 30 days for corrections")
    print("  ✓ Detect ranking changes")
    print("  ✓ Skip unchanged content")
    print("\nEstimated time: <1 minute (skips unchanged)\n")

    proceed = input("Continue? (y/n): ").lower()
    if proceed != 'y':
        print("Skipped.")
        return

    subprocess.run([
        sys.executable,
        "scraper_agent_incremental.py",
        "--lookback", "30"
    ])

    print("\n✓ Incremental update complete!")
    print("  Check 'data_incremental/' folder for results")


def main_menu():
    """Main menu"""
    print("="*70)
    print(" "*15 + "TAEKWONDO SCRAPER AGENT")
    print(" "*15 + "Master Control Interface")
    print("="*70)

    while True:
        print("\nOptions:")
        print("  1. Run Diagnostics (test setup)")
        print("  2. Incremental Update (RECOMMENDED - fast, smart)")
        print("  3. Quick Scrape (1 min - top 3 categories)")
        print("  4. Full Scrape (5 min - all categories)")
        print("  5. Download Files (8 min - Excel/PDF files)")
        print("  6. View Latest Data")
        print("  7. Exit")

        choice = input("\nSelect option (1-7): ").strip()

        if choice == '1':
            run_diagnostics()
        elif choice == '2':
            run_incremental_update()
        elif choice == '3':
            run_quick_scrape()
        elif choice == '4':
            run_full_scrape()
        elif choice == '5':
            run_download_files()
        elif choice == '6':
            view_latest_data()
        elif choice == '7':
            print("\nExiting...")
            break
        else:
            print("Invalid choice. Please select 1-7.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
