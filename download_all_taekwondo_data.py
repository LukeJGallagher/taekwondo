"""
Download All Taekwondo Data
Systematically finds and downloads all available data files from World Taekwondo website
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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaekwondoDataDownloader:
    """Download all available data files from World Taekwondo"""

    def __init__(self, output_dir="taekwondo_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "results").mkdir(exist_ok=True)
        (self.output_dir / "documents").mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        self.downloaded_files: Set[str] = set()
        self.file_links: List[Dict] = []

    def crawl_page_for_files(self, url: str, depth: int = 0, max_depth: int = 1) -> List[Dict]:
        """
        Crawl a page and find all downloadable files
        Optionally follow links to find more files
        """
        if depth > max_depth:
            return []

        print(f"{'  ' * depth}Crawling: {url}")

        try:
            response = self.session.get(url, verify=False, timeout=15)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            found_files = []

            # Find all links
            for link in soup.find_all('a', href=True):
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

                    # Try to extract year from filename or link text
                    year_match = re.search(r'20\d{2}', text + href)
                    if year_match:
                        file_info['year'] = int(year_match.group())

                    found_files.append(file_info)
                    print(f"{'  ' * (depth + 1)}[FOUND] {file_info['filename']}")

                # If depth allows, follow relevant links
                elif depth < max_depth and any(keyword in href.lower() for keyword in
                                                ['ranking', 'result', 'competition', 'document', 'download']):
                    # Avoid going too deep or to external sites
                    if 'worldtaekwondo.org' in absolute_url and absolute_url not in [url]:
                        time.sleep(0.3)
                        found_files.extend(self.crawl_page_for_files(absolute_url, depth + 1, max_depth))

            return found_files

        except Exception as e:
            print(f"{'  ' * depth}  [ERROR] {e}")
            return []

    def explore_file_directory(self, base_path: str, years: List[int]) -> List[Dict]:
        """
        Try to systematically explore a file directory structure
        """
        print(f"\nExploring directory: {base_path}")
        found_files = []

        for year in years:
            print(f"  Checking year {year}...")

            # Try different month formats
            for month in range(1, 13):
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December']

                # Try various file name patterns
                patterns = [
                    f"{base_path}{year}/World_Ranking_{month_names[month-1]}_{year}.xlsx",
                    f"{base_path}{year}/World_Para_Ranking_{month_names[month-1]}_{year}.xlsx",
                    f"{base_path}{year}/Ranking_{month_names[month-1]}_{year}.xlsx",
                    f"{base_path}{year}/Olympic_Ranking_{month_names[month-1]}_{year}.xlsx",
                    f"{base_path}{year}/{month:02d}/ranking.xlsx",
                    f"{base_path}{year}/{month:02d}/results.pdf",
                ]

                for pattern in patterns:
                    full_url = f"https://www.worldtaekwondo.org{pattern}"

                    try:
                        response = self.session.head(full_url, verify=False, timeout=3)
                        if response.status_code == 200:
                            file_info = {
                                'url': full_url,
                                'filename': os.path.basename(pattern),
                                'year': year,
                                'month': month,
                                'file_type': pattern.split('.')[-1].lower()
                            }
                            found_files.append(file_info)
                            print(f"    [FOUND] {file_info['filename']}")

                    except:
                        pass

                time.sleep(0.1)

        return found_files

    def download_file(self, file_info: Dict) -> bool:
        """Download a single file"""
        url = file_info['url']
        filename = file_info['filename']

        # Determine subdirectory based on file type or content
        if 'ranking' in filename.lower() or file_info.get('category') == 'ranking':
            subdir = "rankings"
        elif 'competition' in filename.lower() or 'result' in filename.lower():
            subdir = "competitions"
        else:
            subdir = "documents"

        # Add year prefix if available
        if file_info.get('year'):
            filename = f"{file_info['year']}_{filename}"

        filepath = self.output_dir / subdir / filename

        # Skip if already downloaded
        if filepath.exists() or url in self.downloaded_files:
            print(f"  [SKIP] {filename}")
            return True

        try:
            print(f"  [DL] {filename}...")
            response = self.session.get(url, verify=False, timeout=30, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  [OK] Downloaded: {filename} ({size_mb:.2f} MB)")

            self.downloaded_files.add(url)
            return True

        except Exception as e:
            print(f"  [ERROR] {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False

    def scrape_all_data(self, year_from: int = 2015):
        """Main method to scrape all data"""
        print("=" * 70)
        print("TAEKWONDO DATA DOWNLOADER - ALL YEARS")
        print("=" * 70)

        current_year = datetime.now().year
        years = list(range(year_from, current_year + 1))

        all_files = []

        # Strategy 1: Crawl main pages
        print("\n[1] Crawling website pages for downloadable files...")

        pages_to_crawl = [
            "https://www.worldtaekwondo.org/athletes/Ranking/contents",
            "https://www.worldtaekwondo.org/competitions/overview",
            "https://www.worldtaekwondo.org/competitions/RECORD&STATS/contents",
        ]

        for page_url in pages_to_crawl:
            files = self.crawl_page_for_files(page_url, depth=0, max_depth=1)
            all_files.extend(files)
            time.sleep(1)

        # Strategy 2: Systematically explore file directories
        print("\n[2] Exploring file directories...")

        directory_paths = [
            "/att_file_up/athletes/",
            "/att_file_up/competitions/",
            "/wp-content/uploads/",
        ]

        for dir_path in directory_paths:
            files = self.explore_file_directory(dir_path, years)
            all_files.extend(files)

        # Strategy 3: Check specific competition pages
        print("\n[3] Checking competition-specific pages...")

        # Try to get competition list
        for year in years:
            comp_url = f"https://www.worldtaekwondo.org/competitions/results/{year}"
            try:
                response = self.session.get(comp_url, verify=False, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find result PDFs
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '.pdf' in href.lower() or '.xlsx' in href.lower():
                            absolute_url = urljoin(comp_url, href)
                            file_info = {
                                'url': absolute_url,
                                'filename': os.path.basename(urlparse(absolute_url).path),
                                'year': year,
                                'file_type': href.split('.')[-1].lower(),
                                'category': 'competition'
                            }
                            all_files.append(file_info)

            except:
                pass

            time.sleep(0.5)

        # Remove duplicates
        unique_files = {f['url']: f for f in all_files}.values()
        all_files = list(unique_files)

        print(f"\n{'='*70}")
        print(f"FOUND {len(all_files)} FILES")
        print(f"{'='*70}")

        # Save file list
        files_df = pd.DataFrame(all_files)
        files_list_path = self.output_dir / f"files_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        files_df.to_csv(files_list_path, index=False)
        print(f"\nFile list saved to: {files_list_path}")

        # Download all files
        print(f"\n[4] Downloading files...")
        print("=" * 70)

        successful = 0
        failed = 0

        for i, file_info in enumerate(all_files, 1):
            print(f"\n[{i}/{len(all_files)}] {file_info['filename']}")
            if self.download_file(file_info):
                successful += 1
            else:
                failed += 1

            time.sleep(0.5)

        # Summary
        print("\n" + "=" * 70)
        print("DOWNLOAD SUMMARY")
        print("=" * 70)
        print(f"Total files found: {len(all_files)}")
        print(f"Successfully downloaded: {successful}")
        print(f"Failed: {failed}")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("=" * 70)

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_found': len(all_files),
            'downloaded': successful,
            'failed': failed,
            'year_range': f"{year_from}-{current_year}",
            'files': all_files
        }

        summary_path = self.output_dir / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download all Taekwondo data files')
    parser.add_argument('--year-from', type=int, default=2015,
                        help='Start year (default: 2015)')
    parser.add_argument('--output', default='taekwondo_data',
                        help='Output directory (default: taekwondo_data)')

    args = parser.parse_args()

    downloader = TaekwondoDataDownloader(output_dir=args.output)
    downloader.scrape_all_data(year_from=args.year_from)


if __name__ == "__main__":
    main()
