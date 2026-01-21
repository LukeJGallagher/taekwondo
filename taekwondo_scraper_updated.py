"""
Updated Taekwondo Data Scraper - 2025
Works with the new World Taekwondo website structure using SimplyCompete platform
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaekwondoScraperUpdated:
    """
    Updated scraper for World Taekwondo data
    New website uses SimplyCompete platform: https://worldtkd.simplycompete.com
    """

    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "athletes").mkdir(exist_ok=True)
        (self.output_dir / "rankings").mkdir(exist_ok=True)

        self.session = requests.Session()

        # Updated headers to mimic browser access from worldtaekwondo.org
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.worldtaekwondo.org/',
            'Origin': 'https://www.worldtaekwondo.org',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        })

        # SimplyCompete API base URL
        self.api_base = "https://worldtkd.simplycompete.com"

        # Known ranking category IDs (from URL analysis)
        # These may need to be updated - we'll try to discover them dynamically
        self.ranking_categories = {
            'M-58kg': '11ef3918-68c6-28dd-8999-023374a4dcc1',
            # Add more as discovered
        }

    def get_api_data(self, url: str, add_referer: bool = True) -> Optional[Dict]:
        """Fetch data from SimplyCompete API"""
        try:
            headers = self.session.headers.copy()
            if add_referer:
                headers['Referer'] = 'https://www.worldtaekwondo.org/athletes/Ranking/contents'

            print(f"Fetching: {url}")
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            response.raise_for_status()

            # Try to parse as JSON first
            try:
                return response.json()
            except:
                # If not JSON, return text wrapped in dict
                return {'html': response.text}

        except requests.exceptions.HTTPError as e:
            print(f"  [ERROR] HTTP {e.response.status_code}: {e}")
            return None
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    def scrape_rankings_simplycompete(self, year: int = 2025, month: int = None) -> pd.DataFrame:
        """
        Scrape rankings from SimplyCompete platform

        Args:
            year: Year for rankings (default: current year)
            month: Month for rankings (default: current month)
        """
        print(f"\n[1] Scraping Rankings from SimplyCompete (Year: {year})...")

        if month is None:
            month = datetime.now().month

        all_rankings = []

        # We need to discover category IDs first
        # Try the known endpoint structure
        ranking_types_url = f"{self.api_base}/rankingTypes"

        # Try to get ranking types/categories
        ranking_data = self.get_api_data(ranking_types_url)

        if ranking_data:
            print(f"  [OK] Retrieved ranking configuration")
            # Save raw response for analysis
            debug_file = self.output_dir / "rankings" / f"ranking_config_{datetime.now().strftime('%Y%m%d')}.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(ranking_data, f, indent=2, ensure_ascii=False)

        # Try the specific ranking endpoint (using the URL you provided as template)
        # We'll need to iterate through different category combinations

        # For now, let's try a simpler approach - get rankings page directly
        rankings_page_url = f"{self.api_base}/playerRankingV2"

        page_data = self.get_api_data(rankings_page_url)

        if page_data:
            print(f"  [OK] Retrieved rankings page")
            # Save for analysis
            debug_file = self.output_dir / "rankings" / f"rankings_raw_{datetime.now().strftime('%Y%m%d')}.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)

        # Alternative: Try the specific rankings API endpoint
        # Using pagination
        for page_no in range(1, 6):  # Try first 5 pages
            rankings_url = (
                f"{self.api_base}/rankingsV2?"
                f"embedded=true&"
                f"limit=100&"
                f"month={month}&"
                f"pageNo={page_no}&"
                f"year={year}"
            )

            data = self.get_api_data(rankings_url)

            if data and isinstance(data, dict):
                # Parse the response
                if 'rankings' in data:
                    all_rankings.extend(data['rankings'])
                elif 'data' in data:
                    all_rankings.extend(data['data'])
                else:
                    # Save unknown structure for analysis
                    debug_file = self.output_dir / "rankings" / f"rankings_page{page_no}_debug.json"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  [INFO] Saved page {page_no} data for analysis")

            time.sleep(0.5)

        if all_rankings:
            df = pd.DataFrame(all_rankings)
            output_file = self.output_dir / "rankings" / f"world_rankings_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)
            print(f"  [OK] Saved {len(df)} rankings to {output_file}")
            return df
        else:
            print(f"  [WARN] No rankings data extracted - check debug files in {self.output_dir / 'rankings'}")
            return pd.DataFrame()

    def scrape_competitions_simplycompete(self, page_size: int = 50) -> List[Dict]:
        """
        Scrape competitions from SimplyCompete platform

        Args:
            page_size: Number of items per page
        """
        print("\n[2] Scraping Competitions from SimplyCompete...")

        competitions = []

        for page_no in range(1, 6):  # Try first 5 pages
            url = (
                f"{self.api_base}/events?"
                f"eventType=All&"
                f"invitationStatus=all&"
                f"isArchived=false&"
                f"pageNumber={page_no}&"
                f"itemsPerPage={page_size}"
            )

            data = self.get_api_data(url)

            if data and isinstance(data, dict):
                # Save raw data for analysis
                if page_no == 1:
                    debug_file = self.output_dir / "competitions" / f"competitions_structure.json"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                # Try to extract competitions
                if 'events' in data:
                    competitions.extend(data['events'])
                elif 'data' in data:
                    competitions.extend(data['data'])
                elif 'items' in data:
                    competitions.extend(data['items'])

                # Check if there are more pages
                if data.get('hasMore') == False or data.get('total', 0) <= len(competitions):
                    break

            time.sleep(0.5)

        if competitions:
            # Save to JSON
            output_file = self.output_dir / "competitions" / f"competitions_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(competitions, f, indent=2, ensure_ascii=False)

            # Also save as CSV for easy viewing
            df = pd.DataFrame(competitions)
            csv_file = self.output_dir / "competitions" / f"competitions_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(csv_file, index=False)

            print(f"  [OK] Found {len(competitions)} competitions")
            return competitions
        else:
            print(f"  [WARN] No competitions found")
            return []

    def scrape_saudi_athletes(self, country_code: str = "KSA") -> pd.DataFrame:
        """
        Search for Saudi Arabian athletes

        Args:
            country_code: ISO country code (KSA for Saudi Arabia)
        """
        print(f"\n[3] Searching for {country_code} athletes...")

        # Try athlete search endpoint
        search_url = f"{self.api_base}/players?country={country_code}"

        data = self.get_api_data(search_url)

        athletes = []

        if data and isinstance(data, dict):
            # Save structure for analysis
            debug_file = self.output_dir / "athletes" / f"athletes_structure.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Try to extract athlete list
            if 'players' in data:
                athletes = data['players']
            elif 'data' in data:
                athletes = data['data']
            elif 'athletes' in data:
                athletes = data['athletes']

        if athletes:
            df = pd.DataFrame(athletes)
            output_file = self.output_dir / "athletes" / f"saudi_athletes_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)
            print(f"  [OK] Found {len(df)} athletes")
            return df
        else:
            print(f"  [WARN] No athletes found - check structure file")
            return pd.DataFrame()

    def test_api_endpoints(self):
        """
        Test various API endpoints to discover the correct structure
        """
        print("\n[TEST MODE] Testing SimplyCompete API endpoints...")
        print("=" * 70)

        test_urls = [
            # Rankings endpoints
            f"{self.api_base}/rankingTypes",
            f"{self.api_base}/playerRankingV2",
            f"{self.api_base}/rankings",

            # Events endpoints
            f"{self.api_base}/events?pageNumber=1&itemsPerPage=10",
            f"{self.api_base}/events?eventType=All&pageNumber=1&itemsPerPage=10",

            # Athletes endpoints
            f"{self.api_base}/players",
            f"{self.api_base}/athletes",
        ]

        test_results = []

        for url in test_urls:
            print(f"\nTesting: {url}")
            data = self.get_api_data(url)

            result = {
                'url': url,
                'status': 'Success' if data else 'Failed',
                'data_type': type(data).__name__ if data else None,
            }

            if data and isinstance(data, dict):
                result['keys'] = list(data.keys())[:10]  # First 10 keys

                # Save successful responses
                filename = url.split(self.api_base)[1].replace('/', '_').replace('?', '_')
                debug_file = self.output_dir / f"test_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                result['saved_to'] = str(debug_file)

            test_results.append(result)
            time.sleep(0.5)

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY:")
        print("=" * 70)
        for result in test_results:
            status_icon = "[OK]" if result['status'] == 'Success' else "[FAIL]"
            print(f"{status_icon} {result['url']}")
            if result.get('keys'):
                print(f"      Keys: {', '.join(result['keys'][:5])}")

        return test_results

    def run_full_scrape(self):
        """Run comprehensive data collection with new API"""
        print("=" * 70)
        print("TAEKWONDO DATA SCRAPER - Updated for 2025")
        print("Using SimplyCompete Platform API")
        print("=" * 70)

        # 1. Scrape rankings
        rankings_df = self.scrape_rankings_simplycompete()

        # 2. Scrape competitions
        competitions = self.scrape_competitions_simplycompete()

        # 3. Scrape Saudi athletes
        saudi_df = self.scrape_saudi_athletes()

        print("\n" + "=" * 70)
        print("SCRAPING COMPLETE")
        print(f"Rankings: {len(rankings_df)} entries")
        print(f"Competitions: {len(competitions)} entries")
        print(f"Saudi Athletes: {len(saudi_df)} entries")
        print(f"Data saved to: {self.output_dir.absolute()}")
        print("=" * 70)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='World Taekwondo Data Scraper (Updated 2025)')
    parser.add_argument('--test', action='store_true', help='Run in test mode to discover API endpoints')
    parser.add_argument('--output', default='data', help='Output directory for scraped data')

    args = parser.parse_args()

    scraper = TaekwondoScraperUpdated(output_dir=args.output)

    if args.test:
        scraper.test_api_endpoints()
    else:
        scraper.run_full_scrape()


if __name__ == "__main__":
    main()
