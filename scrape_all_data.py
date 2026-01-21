"""
Master Script - Scrape ALL Taekwondo Data
Runs all scraping methods to collect comprehensive data from all years
SMART UPDATE: Only scrapes new data since last run
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


class MasterTaekwondoScraper:
    """Orchestrates all scraping operations with smart updates"""

    def __init__(self, year_from=2015, force_full=False):
        self.year_from = year_from
        self.current_year = datetime.now().year
        self.base_dir = Path(__file__).parent
        self.start_time = time.time()
        self.force_full = force_full

        # Metadata file to track scraping history
        self.metadata_file = self.base_dir / ".scrape_metadata.json"
        self.metadata = self.load_metadata()

        # Results tracking
        self.results = {
            'downloadable_files': 0,
            'ranking_data': 0,
            'competition_data': 0,
            'errors': [],
            'mode': 'full' if force_full else 'auto'
        }

    def load_metadata(self):
        """Load scraping history metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_metadata(self):
        """Save scraping history metadata"""
        self.metadata['last_scrape'] = datetime.now().isoformat()
        self.metadata['last_full_scrape'] = self.metadata.get('last_full_scrape', datetime.now().isoformat())
        self.metadata['scrape_count'] = self.metadata.get('scrape_count', 0) + 1
        self.metadata['results'] = self.results

        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def get_update_mode(self):
        """Determine if we need full scrape or just update"""
        if self.force_full:
            return 'full', None

        if 'last_scrape' not in self.metadata:
            return 'full', None

        last_scrape = datetime.fromisoformat(self.metadata['last_scrape'])
        days_since = (datetime.now() - last_scrape).days

        # Full scrape if:
        # - Never scraped before
        # - Last scrape was more than 7 days ago
        # - Last scrape failed
        if days_since > 7 or self.metadata.get('results', {}).get('errors'):
            return 'full', last_scrape

        # Otherwise, incremental update
        return 'incremental', last_scrape

    def print_header(self, message):
        """Print formatted section header"""
        print("\n" + "=" * 70)
        print(f"  {message}")
        print("=" * 70 + "\n")

    def run_script(self, script_name, description, args=None):
        """Run a Python script and capture results"""
        self.print_header(description)

        script_path = self.base_dir / script_name

        if not script_path.exists():
            print(f"[WARNING] {script_name} not found, skipping...")
            self.results['errors'].append(f"{script_name} not found")
            return False

        try:
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)

            print(f"Running: {' '.join(cmd)}")
            print("-" * 70)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Print output
            if result.stdout:
                print(result.stdout)

            if result.stderr and "ERROR" in result.stderr.upper():
                print("ERRORS:")
                print(result.stderr)

            if result.returncode == 0:
                print(f"\n[OK] {description} - COMPLETED")
                return True
            else:
                print(f"\n[ERROR] {description} - FAILED (exit code: {result.returncode})")
                self.results['errors'].append(f"{script_name} failed")
                return False

        except subprocess.TimeoutExpired:
            print(f"\n[TIMEOUT] {description} - TIMEOUT (exceeded 10 minutes)")
            self.results['errors'].append(f"{script_name} timeout")
            return False

        except Exception as e:
            print(f"\n[ERROR] {description} - ERROR: {e}")
            self.results['errors'].append(f"{script_name}: {str(e)}")
            return False

    def check_selenium_installed(self):
        """Check if Selenium is installed"""
        try:
            import selenium
            return True
        except ImportError:
            return False

    def get_incremental_year(self, last_scrape):
        """Determine which year to start incremental scrape from"""
        if last_scrape is None:
            return self.year_from

        # Start from last scrape year, or current year if within same year
        last_year = last_scrape.year

        # If last scrape was this year, only update current year
        if last_year == self.current_year:
            return self.current_year

        # Otherwise start from last year to catch any updates
        return max(last_year - 1, self.year_from)

    def run_all(self):
        """Execute all scraping operations"""
        # Determine update mode
        mode, last_scrape = self.get_update_mode()
        self.results['mode'] = mode

        print("=" * 70)
        print(" " * 15 + "TAEKWONDO MASTER DATA SCRAPER")
        print(" " * 15 + "Smart Update System")
        print("=" * 70)

        print(f"\nWorking Directory: {self.base_dir}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show update mode
        if mode == 'full':
            print(f"\nMode: FULL SCRAPE")
            print(f"Date Range: {self.year_from} - {self.current_year}")
            if last_scrape:
                days_ago = (datetime.now() - last_scrape).days
                print(f"   (Last scrape was {days_ago} days ago)")
            year_start = self.year_from
        else:
            print(f"\nMode: INCREMENTAL UPDATE")
            print(f"Last Scrape: {last_scrape.strftime('%Y-%m-%d %H:%M:%S')}")
            days_ago = (datetime.now() - last_scrape).days
            print(f"   ({days_ago} days ago)")
            year_start = self.get_incremental_year(last_scrape)
            print(f"Update Range: {year_start} - {self.current_year}")

        # Phase 1: Quick Test (always run to check connectivity)
        self.run_script(
            'quick_test.py',
            'PHASE 1: Testing Endpoints & Connectivity'
        )

        time.sleep(2)

        # Phase 2: Download Available Files
        success = self.run_script(
            'download_all_taekwondo_data.py',
            f'PHASE 2: Downloading Files (from {year_start})',
            args=['--year-from', str(year_start)]
        )

        if success:
            self.results['downloadable_files'] = self.count_downloaded_files()

        time.sleep(2)

        # Phase 3: Selenium Scraper (if available)
        selenium_available = self.check_selenium_installed()

        if selenium_available:
            print("\nSelenium is available - running browser automation...")

            success = self.run_script(
                'taekwondo_scraper_selenium.py',
                'PHASE 3: Selenium Browser Automation (Current Rankings)',
                args=['--headless']
            )

            if success:
                self.results['ranking_data'] += 1
        else:
            print("\n[SKIP] Skipping Selenium scraper (not installed)")
            print("   Install with: pip install selenium webdriver-manager")
            self.results['errors'].append("Selenium not available")

        # Save metadata before summary
        self.save_metadata()

        # Generate summary
        self.generate_summary()

    def count_downloaded_files(self):
        """Count files in data directories"""
        count = 0

        # Check multiple possible data directories
        for dirname in ['taekwondo_data', 'data', 'data_all_years']:
            data_dir = self.base_dir / dirname
            if data_dir.exists():
                for subdir in ['rankings', 'competitions', 'downloads', 'documents', 'results']:
                    subdir_path = data_dir / subdir
                    if subdir_path.exists():
                        count += len(list(subdir_path.glob('*.*')))

        return count

    def generate_summary(self):
        """Print final summary"""
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        self.print_header("FINAL SUMMARY")

        print(f"Scrape Mode: {self.results['mode'].upper()}")
        print(f"Total Time: {minutes}m {seconds}s")
        print(f"Files Downloaded: {self.results['downloadable_files']}")
        print(f"Total Scrapes: {self.metadata.get('scrape_count', 0)}")

        if self.results['errors']:
            print(f"\n[WARNING] Errors: {len(self.results['errors'])}")
            for error in self.results['errors'][:5]:  # Show first 5
                print(f"   - {error}")
        else:
            print("\n[SUCCESS] All operations completed successfully!")

        # Check data directories
        print("\nData Locations:")
        for dirname in ['data', 'taekwondo_data', 'data_all_years']:
            dirpath = self.base_dir / dirname
            if dirpath.exists():
                file_count = sum(1 for _ in dirpath.rglob('*.*'))
                size_mb = sum(f.stat().st_size for f in dirpath.rglob('*.*') if f.is_file()) / (1024 * 1024)
                print(f"   - {dirname}/: {file_count} files ({size_mb:.1f} MB)")

        # Show what was updated
        print("\nUpdated Today:")
        today = datetime.now().date()
        for dirname in ['data', 'taekwondo_data']:
            dirpath = self.base_dir / dirname
            if dirpath.exists():
                for filepath in dirpath.rglob('*.csv'):
                    if filepath.stat().st_mtime:
                        mtime = datetime.fromtimestamp(filepath.stat().st_mtime).date()
                        if mtime == today:
                            print(f"   - {filepath.name}")

        # Next steps
        print("\nNext Steps:")
        print("   1. Review collected data in data directories")
        print("   2. Run analysis: python performance_analyzer.py")
        print("   3. Launch dashboard: streamlit run dashboard.py")

        # Schedule next update
        print("\nNext Update Recommendation:")
        if self.results['mode'] == 'incremental':
            print("   Run daily for continuous updates:")
            print("   python scrape_all_data.py")
        else:
            print("   Weekly updates recommended:")
            print("   python scrape_all_data.py  (auto-detects incremental)")

        # Force full scrape reminder
        print("\nForce Full Scrape:")
        print("   python scrape_all_data.py --force-full")

        # Recommendations
        if not self.check_selenium_installed():
            print("\nRecommendation:")
            print("   Install Selenium for maximum data collection:")
            print("   pip install selenium webdriver-manager")

        print("\n" + "=" * 70)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Master Taekwondo Data Scraper - Smart Update System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SMART UPDATE SYSTEM:
This script automatically detects what needs to be scraped:
  - First run: Full scrape from specified year
  - Subsequent runs: Incremental updates (only new data)
  - Weekly: Automatic full refresh if >7 days since last scrape

Scraping Methods:
  1. Tests endpoint accessibility
  2. Downloads all available Excel/PDF files
  3. Runs Selenium browser automation (if installed)
  4. Updates metadata for smart future updates

Examples:
  # Smart update (auto-detects if full or incremental needed)
  python scrape_all_data.py

  # Force full scrape from 2015
  python scrape_all_data.py --force-full

  # Force full scrape from 2020
  python scrape_all_data.py --force-full --year-from 2020

  # Daily incremental updates (recommended in cron/scheduled task)
  python scrape_all_data.py
        """
    )

    parser.add_argument(
        '--year-from',
        type=int,
        default=2015,
        help='Start year for full scrape (default: 2015)'
    )

    parser.add_argument(
        '--force-full',
        action='store_true',
        help='Force full scrape (ignore last scrape date)'
    )

    args = parser.parse_args()

    # Validate year
    current_year = datetime.now().year
    if args.year_from < 2000 or args.year_from > current_year:
        print(f"[ERROR] Invalid year: {args.year_from}")
        print(f"   Please use a year between 2000 and {current_year}")
        sys.exit(1)

    # Run master scraper
    try:
        scraper = MasterTaekwondoScraper(
            year_from=args.year_from,
            force_full=args.force_full
        )
        scraper.run_all()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Interrupted by user")
        print("   Partial data may have been collected - check data directories")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
