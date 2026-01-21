"""
Download All Taekwondo Data - FIXED VERSION
Enhanced with:
1. Smart timeout handling (skip stuck files instead of hanging)
2. Progress tracking with time limits
3. File existence pre-check to avoid wasted requests
4. Maximum iterations to prevent infinite loops
"""

import os
import re
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import urllib3
import signal
from contextlib import contextmanager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    """Context manager for timeout handling"""
    def signal_handler(signum, frame):
        raise TimeoutException("Operation timed out")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class EnhancedTaekwondoDataDownloader:
    """Download all available data files with smart timeout handling"""

    def __init__(self, output_dir="taekwondo_data", max_runtime_minutes=8):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "results").mkdir(exist_ok=True)
        (self.output_dir / "documents").mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        self.downloaded_files: Set[str] = set()
        self.file_links: List[Dict] = []

        # Timeout control
        self.max_runtime_minutes = max_runtime_minutes
        self.start_time = time.time()
        self.max_crawl_depth_iterations = 50  # Prevent infinite loops

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'files_found': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'errors': 0,
            'timeouts': 0
        }

    def check_runtime_limit(self):
        """Check if we've exceeded max runtime"""
        elapsed_minutes = (time.time() - self.start_time) / 60
        if elapsed_minutes > self.max_runtime_minutes:
            print(f"\n[TIMEOUT] Exceeded max runtime ({self.max_runtime_minutes} min)")
            return False
        return True

    def quick_check_url_exists(self, url: str) -> bool:
        """Quick HEAD request to check if URL exists (with timeout)"""
        try:
            response = self.session.head(url, verify=False, timeout=2, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

    def crawl_page_for_files(self, url: str, depth: int = 0, max_depth: int = 1) -> List[Dict]:
        """
        Crawl a page and find all downloadable files
        WITH TIMEOUT PROTECTION
        """
        if depth > max_depth:
            return []

        if not self.check_runtime_limit():
            print(f"  [SKIP] Runtime limit reached, stopping crawl")
            return []

        if self.stats['pages_crawled'] >= self.max_crawl_depth_iterations:
            print(f"  [SKIP] Max crawl iterations reached ({self.max_crawl_depth_iterations})")
            return []

        print(f"{'  ' * depth}Crawling: {url}")
        self.stats['pages_crawled'] += 1

        try:
            # Short timeout for page fetching
            response = self.session.get(url, verify=False, timeout=10)
            if response.status_code != 200:
                print(f"{'  ' * depth}  [SKIP] Status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            found_files = []

            # Find all links
            links = soup.find_all('a', href=True)
            print(f"{'  ' * depth}  Found {len(links)} links")

            for link in links[:100]:  # Limit links per page
                if not self.check_runtime_limit():
                    break

                href = link['href']
                text = link.get_text(strip=True)
                absolute_url = urljoin(url, href)

                # Check if it's a downloadable file
                file_extensions = ['.pdf', '.xlsx', '.xls', '.csv', '.doc', '.docx', '.zip']
                if any(ext in href.lower() for ext in file_extensions):
                    file_info = {
                        'url': absolute_url,
                        'filename': os.path.basename(urlparse(absolute_url).path),
                        'link_text': text,
                        'source_page': url,
                        'file_type': href.split('.')[-1].lower()
                    }

                    # Try to extract year
                    year_match = re.search(r'20\d{2}', text + href)
                    if year_match:
                        file_info['year'] = int(year_match.group())

                    found_files.append(file_info)
                    self.stats['files_found'] += 1
                    print(f"{'  ' * (depth + 1)}[FOUND] {file_info['filename']}")

                # Follow relevant links (only if within limit)
                elif depth < max_depth and self.stats['pages_crawled'] < self.max_crawl_depth_iterations:
                    if any(keyword in href.lower() for keyword in
                           ['ranking', 'result', 'competition', 'document', 'download']):
                        if 'worldtaekwondo.org' in absolute_url and absolute_url != url:
                            time.sleep(0.3)
                            found_files.extend(self.crawl_page_for_files(absolute_url, depth + 1, max_depth))

            return found_files

        except requests.Timeout:
            print(f"{'  ' * depth}  [TIMEOUT] Page fetch timed out")
            self.stats['timeouts'] += 1
            return []
        except Exception as e:
            print(f"{'  ' * depth}  [ERROR] {str(e)[:80]}")
            self.stats['errors'] += 1
            return []

    def explore_file_directory_smart(self, base_path: str, years: List[int], max_checks=100) -> List[Dict]:
        """
        Smart directory exploration with check limits
        """
        print(f"\nExploring directory: {base_path}")
        found_files = []
        checks_done = 0

        for year in years:
            if not self.check_runtime_limit() or checks_done >= max_checks:
                print(f"  [STOP] Limit reached (runtime or max checks)")
                break

            print(f"  Checking year {year}...")

            # Only check recent months for current year
            if year == datetime.now().year:
                months_to_check = range(1, datetime.now().month + 1)
            else:
                months_to_check = [5, 6, 11, 12]  # Mid-year and end-of-year only

            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December']

            for month in months_to_check:
                if checks_done >= max_checks:
                    break

                # Most likely patterns only
                patterns = [
                    f"{base_path}{year}/World_Ranking_{month_names[month-1]}_{year}.xlsx",
                    f"{base_path}{year}/World_Para_Ranking_{month_names[month-1]}_{year}.xlsx",
                ]

                for pattern in patterns:
                    checks_done += 1
                    full_url = f"https://www.worldtaekwondo.org{pattern}"

                    try:
                        # Quick HEAD check with short timeout
                        response = self.session.head(full_url, verify=False, timeout=2)
                        if response.status_code == 200:
                            file_info = {
                                'url': full_url,
                                'filename': os.path.basename(pattern),
                                'year': year,
                                'month': month,
                                'file_type': pattern.split('.')[-1].lower()
                            }
                            found_files.append(file_info)
                            self.stats['files_found'] += 1
                            print(f"    [FOUND] {file_info['filename']}")
                    except:
                        pass

                    time.sleep(0.05)  # Brief delay

        print(f"  Completed {checks_done} checks")
        return found_files

    def download_file(self, file_info: Dict) -> bool:
        """Download a single file with timeout protection"""
        url = file_info['url']
        filename = file_info['filename']

        # Determine subdirectory
        if 'ranking' in filename.lower():
            subdir = "rankings"
        elif 'competition' in filename.lower() or 'result' in filename.lower():
            subdir = "competitions"
        else:
            subdir = "documents"

        # Add year prefix if available
        if file_info.get('year'):
            filename = f"{file_info['year']}_{filename}"

        filepath = self.output_dir / subdir / filename

        # Skip if already exists
        if filepath.exists() or url in self.downloaded_files:
            print(f"  [SKIP] Already have {filename}")
            self.stats['files_skipped'] += 1
            return True

        try:
            print(f"  [DL] {filename}...")
            # Stream download with timeout
            response = self.session.get(url, verify=False, timeout=15, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  [OK] {filename} ({size_mb:.2f} MB)")

            self.downloaded_files.add(url)
            self.stats['files_downloaded'] += 1
            return True

        except requests.Timeout:
            print(f"  [TIMEOUT] Download timed out")
            self.stats['timeouts'] += 1
            if filepath.exists():
                filepath.unlink()
            return False
        except Exception as e:
            print(f"  [ERROR] {str(e)[:80]}")
            self.stats['errors'] += 1
            if filepath.exists():
                filepath.unlink()
            return False

    def scrape_all_data(self, year_from: int = 2020):
        """Main method with smart timeout handling"""
        print("=" * 70)
        print("ENHANCED TAEKWONDO DATA DOWNLOADER")
        print(f"Max Runtime: {self.max_runtime_minutes} minutes")
        print("=" * 70)

        current_year = datetime.now().year
        years = list(range(year_from, current_year + 1))

        all_files = []

        # Strategy 1: Crawl main pages (LIMITED)
        print("\n[PHASE 1] Crawling main pages (limited depth)...")
        pages_to_crawl = [
            "https://www.worldtaekwondo.org/athletes/Ranking/contents",
        ]

        for page_url in pages_to_crawl:
            if not self.check_runtime_limit():
                break
            files = self.crawl_page_for_files(page_url, depth=0, max_depth=0)  # No deep crawl
            all_files.extend(files)
            time.sleep(1)

        # Strategy 2: Smart directory exploration (LIMITED)
        print("\n[PHASE 2] Smart directory exploration...")
        directory_paths = [
            "/att_file_up/athletes/",
        ]

        for dir_path in directory_paths:
            if not self.check_runtime_limit():
                break
            files = self.explore_file_directory_smart(dir_path, years, max_checks=50)
            all_files.extend(files)

        # Remove duplicates
        unique_files = {f['url']: f for f in all_files}.values()
        all_files = list(unique_files)

        print(f"\n{'='*70}")
        print(f"FOUND {len(all_files)} UNIQUE FILES")
        print(f"{'='*70}")

        if all_files:
            # Save file list
            files_df = pd.DataFrame(all_files)
            files_list_path = self.output_dir / f"files_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            files_df.to_csv(files_list_path, index=False)
            print(f"\nFile list: {files_list_path}")

            # Download files
            print(f"\n[PHASE 3] Downloading files...")
            print("=" * 70)

            for i, file_info in enumerate(all_files, 1):
                if not self.check_runtime_limit():
                    print(f"\n[STOP] Runtime limit reached during downloads")
                    break

                print(f"\n[{i}/{len(all_files)}] {file_info['filename']}")
                self.download_file(file_info)
                time.sleep(0.3)

        # Summary
        elapsed = (time.time() - self.start_time) / 60
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Runtime: {elapsed:.1f} minutes")
        print(f"Pages crawled: {self.stats['pages_crawled']}")
        print(f"Files found: {self.stats['files_found']}")
        print(f"Files downloaded: {self.stats['files_downloaded']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        print(f"Timeouts: {self.stats['timeouts']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\nOutput: {self.output_dir.absolute()}")
        print("=" * 70)

        # Save summary
        import json
        summary = {
            'timestamp': datetime.now().isoformat(),
            'runtime_minutes': elapsed,
            'stats': self.stats,
            'year_range': f"{year_from}-{current_year}",
            'files': all_files
        }

        summary_path = self.output_dir / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed summary: {summary_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Taekwondo Data Downloader with Timeout Protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Smart Features:
  - Maximum runtime limit (default 8 minutes)
  - Skip stuck downloads instead of hanging
  - Limited iterations to prevent infinite loops
  - Smart file discovery (recent years prioritized)

Examples:
  # Default (from 2020, 8 min max)
  python download_all_taekwondo_data_fixed.py

  # Custom year range
  python download_all_taekwondo_data_fixed.py --year-from 2022

  # Longer runtime allowed
  python download_all_taekwondo_data_fixed.py --max-runtime 15
        """
    )

    parser.add_argument('--year-from', type=int, default=2020,
                        help='Start year (default: 2020)')
    parser.add_argument('--max-runtime', type=int, default=8,
                        help='Max runtime in minutes (default: 8)')
    parser.add_argument('--output', default='taekwondo_data',
                        help='Output directory (default: taekwondo_data)')

    args = parser.parse_args()

    downloader = EnhancedTaekwondoDataDownloader(
        output_dir=args.output,
        max_runtime_minutes=args.max_runtime
    )
    downloader.scrape_all_data(year_from=args.year_from)


if __name__ == "__main__":
    main()
