"""
Comprehensive Taekwondo Data Scraper - All Years
Strategy:
1. Try to download Excel/CSV files directly from World Taekwondo
2. Use web scraping to find all available data files
3. Scrape historical competition results
4. Get athlete profiles and rankings for all available years
"""

import os
import re
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ComprehensiveTaekwondoScraper:
    """
    Multi-strategy scraper for comprehensive Taekwondo data collection
    """

    def __init__(self, output_dir="data_all_years"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories by year
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "athletes").mkdir(exist_ok=True)
        (self.output_dir / "downloads").mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        self.downloaded_urls = set()
        self.all_data = {
            'rankings': [],
            'competitions': [],
            'athletes': [],
            'files_downloaded': []
        }

    def download_file(self, url: str, filename: str, subdir: str = "downloads") -> bool:
        """Download a file from URL"""
        filepath = self.output_dir / subdir / filename

        if filepath.exists():
            print(f"  [SKIP] Already exists: {filename}")
            return True

        try:
            print(f"  [DL] Downloading: {filename}")
            response = self.session.get(url, verify=False, timeout=60, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  [OK] Downloaded: {filename} ({size_mb:.2f} MB)")

            self.all_data['files_downloaded'].append({
                'url': url,
                'filename': filename,
                'filepath': str(filepath),
                'size_mb': size_mb,
                'download_date': datetime.now().isoformat()
            })

            return True

        except Exception as e:
            print(f"  [ERROR] {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False

    def find_ranking_excel_files(self) -> List[Dict]:
        """
        Search for ranking Excel files on World Taekwondo website
        These are often published as monthly or annual downloads
        """
        print("\n[1] Searching for downloadable ranking files...")

        potential_urls = []

        # Try various year/month combinations for ranking files
        current_year = datetime.now().year
        years = range(2015, current_year + 1)
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

        # Pattern: /att_file_up/athletes/YEAR/filename.xlsx
        for year in years:
            for month in months:
                # Try various filename patterns
                patterns = [
                    f"/att_file_up/athletes/{year}/World_Ranking_{month}_{year}.xlsx",
                    f"/att_file_up/athletes/{year}/World_Para_Ranking_{month}_{year}.xlsx",
                    f"/att_file_up/athletes/{year}/Ranking_{month}_{year}.xlsx",
                    f"/att_file_up/athletes/{year}/Olympic_Ranking_{month}_{year}.xlsx",
                ]

                for pattern in patterns:
                    url = f"https://www.worldtaekwondo.org{pattern}"
                    potential_urls.append({
                        'url': url,
                        'year': year,
                        'month': month,
                        'type': 'ranking'
                    })

        # Try to download each file
        successful_downloads = []

        for i, file_info in enumerate(potential_urls):
            if i > 0 and i % 20 == 0:
                print(f"  Checked {i}/{len(potential_urls)} potential files...")

            url = file_info['url']
            filename = os.path.basename(urlparse(url).path)

            # Quick HEAD request to check if file exists
            try:
                response = self.session.head(url, verify=False, timeout=5)
                if response.status_code == 200:
                    print(f"  [FOUND] {filename}")
                    if self.download_file(url, filename, "rankings"):
                        successful_downloads.append(file_info)
                    time.sleep(0.5)

            except:
                pass

        print(f"  [OK] Found and downloaded {len(successful_downloads)} ranking files")
        return successful_downloads

    def scrape_historical_competitions(self, year_from: int = 2015, year_to: int = None) -> List[Dict]:
        """
        Try to scrape historical competition data
        """
        if year_to is None:
            year_to = datetime.now().year

        print(f"\n[2] Scraping Historical Competitions ({year_from}-{year_to})...")

        all_competitions = []

        # Try the old and new URL structures
        for year in range(year_from, year_to + 1):
            print(f"  Year {year}...")

            # Try various URL patterns
            url_patterns = [
                f"https://www.worldtaekwondo.org/competitions/results/{year}",
                f"https://www.worldtaekwondo.org/competitions/list/{year}",
                f"https://www.worldtaekwondo.org/results/{year}",
            ]

            for url in url_patterns:
                try:
                    response = self.session.get(url, verify=False, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Look for competition links and downloadable files
                        links = soup.find_all('a', href=True)

                        for link in links:
                            href = link['href']
                            text = link.get_text(strip=True)

                            # Check for PDF result books
                            if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.xls']):
                                absolute_url = urljoin(url, href)

                                comp_data = {
                                    'year': year,
                                    'name': text,
                                    'url': absolute_url,
                                    'file_type': href.split('.')[-1].lower()
                                }

                                all_competitions.append(comp_data)

                                # Download the file
                                filename = f"{year}_{os.path.basename(urlparse(absolute_url).path)}"
                                self.download_file(absolute_url, filename, "competitions")

                        time.sleep(1)
                        break  # If successful, don't try other URL patterns

                except Exception as e:
                    continue

        if all_competitions:
            # Save competition list
            output_file = self.output_dir / "competitions" / "all_competitions_list.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_competitions, f, indent=2, ensure_ascii=False)

            csv_file = self.output_dir / "competitions" / "all_competitions_list.csv"
            pd.DataFrame(all_competitions).to_csv(csv_file, index=False)

            print(f"  [OK] Found {len(all_competitions)} historical competition files")

        self.all_data['competitions'] = all_competitions
        return all_competitions

    def search_wordpress_uploads(self) -> List[Dict]:
        """
        Search WordPress uploads directory for result books and ranking files
        Many sports federations use WordPress and store files in wp-content/uploads
        """
        print("\n[3] Searching WordPress uploads directory...")

        found_files = []

        # Try to access the uploads directory index (if directory listing is enabled)
        base_paths = [
            "https://www.worldtaekwondo.org/wp-content/uploads/",
            "https://www.worldtaekwondo.org/att_file_up/",
        ]

        current_year = datetime.now().year
        years = range(2010, current_year + 1)

        for base_path in base_paths:
            print(f"  Checking: {base_path}")

            for year in years:
                # Try both YYYY and YYYY/MM format
                for month in range(1, 13):
                    url_patterns = [
                        f"{base_path}{year}/",
                        f"{base_path}{year}/{month:02d}/",
                    ]

                    for url in url_patterns:
                        try:
                            response = self.session.get(url, verify=False, timeout=10)

                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, 'html.parser')

                                # Look for file links
                                links = soup.find_all('a', href=True)

                                for link in links:
                                    href = link['href']
                                    text = link.get_text(strip=True)

                                    # Check for relevant files
                                    if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.xls', '.csv']):
                                        # Check if it's a ranking or competition file
                                        if any(keyword in text.lower() or keyword in href.lower()
                                               for keyword in ['ranking', 'result', 'championship', 'competition']):

                                            absolute_url = urljoin(url, href)

                                            file_info = {
                                                'url': absolute_url,
                                                'year': year,
                                                'month': month,
                                                'name': text,
                                                'source': 'wordpress_uploads'
                                            }

                                            found_files.append(file_info)

                                            # Download
                                            filename = f"{year}_{month:02d}_{os.path.basename(urlparse(absolute_url).path)}"
                                            self.download_file(absolute_url, filename, "downloads")

                        except:
                            pass

                        time.sleep(0.2)

        print(f"  [OK] Found {len(found_files)} files in uploads")
        return found_files

    def try_direct_api_access(self) -> Dict:
        """
        Try to access data through any available APIs
        This is a fallback method
        """
        print("\n[4] Attempting alternative data access methods...")

        results = {
            'rankings': None,
            'athletes': None,
            'competitions': None
        }

        # Try old mobile API endpoints (sometimes these still work)
        old_api_urls = [
            "https://m.worldtaekwondo.org/api/ranking",
            "https://m.worldtaekwondo.org/api/athletes",
            "https://m.worldtaekwondo.org/api/competitions",
        ]

        for url in old_api_urls:
            try:
                response = self.session.get(url, verify=False, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    key = url.split('/')[-1]
                    results[key] = data

                    # Save
                    output_file = self.output_dir / f"api_{key}_{datetime.now().strftime('%Y%m%d')}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"  [OK] Retrieved data from {url}")

            except:
                pass

        return results

    def generate_summary_report(self):
        """Generate a summary of all collected data"""
        print("\n[5] Generating summary report...")

        summary = {
            'scrape_date': datetime.now().isoformat(),
            'total_files_downloaded': len(self.all_data['files_downloaded']),
            'total_competitions': len(self.all_data['competitions']),
            'files_by_year': {},
            'files_by_type': {}
        }

        # Analyze downloaded files
        for file_info in self.all_data['files_downloaded']:
            # By year
            year = file_info.get('year', 'unknown')
            if year not in summary['files_by_year']:
                summary['files_by_year'][year] = 0
            summary['files_by_year'][year] += 1

            # By type
            file_type = file_info['filename'].split('.')[-1].lower()
            if file_type not in summary['files_by_type']:
                summary['files_by_type'][file_type] = 0
            summary['files_by_type'][file_type] += 1

        # Save summary
        summary_file = self.output_dir / f"scraping_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Summary saved to {summary_file}")

        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Total files downloaded: {summary['total_files_downloaded']}")
        print(f"Total competitions found: {summary['total_competitions']}")
        print(f"\nFiles by type:")
        for ftype, count in summary['files_by_type'].items():
            print(f"  {ftype.upper()}: {count}")
        print(f"\nFiles by year:")
        for year, count in sorted(summary['files_by_year'].items()):
            print(f"  {year}: {count}")
        print("=" * 70)

        return summary

    def run_comprehensive_scrape(self):
        """Execute all scraping methods"""
        print("=" * 70)
        print("COMPREHENSIVE TAEKWONDO DATA SCRAPER")
        print("Collecting ALL available historical data")
        print("=" * 70)

        start_time = time.time()

        # Strategy 1: Direct downloads of ranking files
        ranking_files = self.find_ranking_excel_files()

        # Strategy 2: Historical competitions
        competitions = self.scrape_historical_competitions(year_from=2015)

        # Strategy 3: WordPress uploads search
        wp_files = self.search_wordpress_uploads()

        # Strategy 4: Alternative API access
        api_data = self.try_direct_api_access()

        # Generate summary
        summary = self.generate_summary_report()

        elapsed_time = time.time() - start_time

        print(f"\n[COMPLETE] Scraping finished in {elapsed_time:.1f} seconds")
        print(f"[FOLDER] All data saved to: {self.output_dir.absolute()}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Comprehensive Taekwondo Data Scraper - All Years',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all data from 2015 onwards (default)
  python taekwondo_comprehensive_scraper.py

  # Scrape from specific year
  python taekwondo_comprehensive_scraper.py --year-from 2010

  # Custom output directory
  python taekwondo_comprehensive_scraper.py --output my_data_folder
        """
    )

    parser.add_argument('--year-from', type=int, default=2015,
                        help='Start year for historical data (default: 2015)')
    parser.add_argument('--output', default='data_all_years',
                        help='Output directory (default: data_all_years)')

    args = parser.parse_args()

    try:
        scraper = ComprehensiveTaekwondoScraper(output_dir=args.output)
        scraper.run_comprehensive_scrape()

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
