"""
World Taekwondo API Scraper
Scrapes data from web.worldtaekwondo.martial.services API
Gets competitions, profiles, statistics, results, medalists, and result books
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import re

class WorldTaekwondoAPIScraper:
    def __init__(self, output_dir="data_wt_api"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://web.worldtaekwondo.martial.services"
        self.api_base = "https://api.worldtaekwondo.martial.services"  # Likely API endpoint

        self.competitions = []
        self.profiles = []
        self.country_stats = []
        self.results = {}
        self.network_logs = []

    def setup_driver_with_logging(self):
        """Setup Chrome with network logging to capture API calls"""
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=options)
        return driver

    def extract_api_calls(self, driver):
        """Extract API calls from browser network logs"""
        print("\n[ANALYZING] Network traffic for API endpoints...")

        logs = driver.get_log('performance')
        api_calls = []

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')

                if 'Network.response' in method or 'Network.request' in method:
                    params = message.get('message', {}).get('params', {})
                    url = params.get('request', {}).get('url', '') or params.get('response', {}).get('url', '')

                    if url and ('api.' in url or '/api/' in url or 'martial.services' in url):
                        api_calls.append({
                            'url': url,
                            'method': params.get('request', {}).get('method', ''),
                            'type': params.get('type', ''),
                        })
            except:
                pass

        # Remove duplicates
        unique_calls = []
        seen_urls = set()
        for call in api_calls:
            if call['url'] not in seen_urls:
                unique_calls.append(call)
                seen_urls.add(call['url'])
                print(f"  Found: {call['url']}")

        return unique_calls

    def scrape_competitions_list(self, driver):
        """Scrape list of all competitions"""
        print(f"\n{'='*70}")
        print("SCRAPING COMPETITIONS LIST")
        print(f"{'='*70}")

        url = f"{self.base_url}/competitions"
        print(f"\nURL: {url}")

        try:
            driver.get(url)
            time.sleep(5)  # Wait for page and API calls

            # Extract API calls
            api_calls = self.extract_api_calls(driver)

            # Save page HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            with open(self.output_dir / "competitions_page.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Parse competitions from page
            competitions = []

            # Look for competition links
            comp_links = soup.find_all('a', href=lambda h: h and '/competitions/' in h)
            print(f"\nFound {len(comp_links)} competition links")

            for link in comp_links:
                comp_data = {
                    'name': link.get_text(strip=True),
                    'url': link.get('href'),
                    'slug': link.get('href', '').split('/')[-1] if '/' in link.get('href', '') else None
                }

                # Try to extract dates
                parent = link.parent
                if parent:
                    text = parent.get_text()
                    # Look for date patterns
                    dates = re.findall(r'\d{1,2}\s+\w+\s+\d{4}', text)
                    if dates:
                        comp_data['dates'] = dates

                competitions.append(comp_data)

            self.competitions = competitions
            print(f"\n[EXTRACTED] {len(competitions)} competitions")

            # Try to find API endpoint by checking network
            for call in api_calls:
                if 'competition' in call['url'].lower():
                    print(f"\n[API FOUND] {call['url']}")

                    # Try to fetch from API
                    try:
                        response = requests.get(call['url'], timeout=10)
                        if response.status_code == 200:
                            api_data = response.json()
                            api_file = self.output_dir / "competitions_api.json"
                            with open(api_file, 'w', encoding='utf-8') as f:
                                json.dump(api_data, f, indent=2)
                            print(f"[SAVED] API data to {api_file.name}")
                    except Exception as e:
                        print(f"[ERROR] Could not fetch API: {e}")

            return competitions

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_competition_details(self, driver, comp_slug):
        """Scrape detailed results for a specific competition"""
        print(f"\n{'='*70}")
        print(f"SCRAPING: {comp_slug}")
        print(f"{'='*70}")

        results_url = f"{self.base_url}/competitions/{comp_slug}/results"
        medalists_url = f"{self.base_url}/competitions/{comp_slug}/medalists"

        comp_data = {
            'slug': comp_slug,
            'results': [],
            'medalists': []
        }

        # Get results
        try:
            print(f"\n[RESULTS] {results_url}")
            driver.get(results_url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save HTML
            with open(self.output_dir / f"comp_{comp_slug}_results.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Extract API calls
            api_calls = self.extract_api_calls(driver)

            # Parse results from page
            tables = soup.find_all('table')
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    comp_data['results'].append(df.to_dict())
                except:
                    pass

            # Try API endpoints
            for call in api_calls:
                if 'result' in call['url'].lower():
                    try:
                        response = requests.get(call['url'], timeout=10)
                        if response.status_code == 200:
                            api_data = response.json()
                            comp_data['results_api'] = api_data
                    except:
                        pass

        except Exception as e:
            print(f"[ERROR] Results: {e}")

        # Get medalists
        try:
            print(f"\n[MEDALISTS] {medalists_url}")
            driver.get(medalists_url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save HTML
            with open(self.output_dir / f"comp_{comp_slug}_medalists.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Extract API calls
            api_calls = self.extract_api_calls(driver)

            # Parse medalists
            tables = soup.find_all('table')
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    comp_data['medalists'].append(df.to_dict())
                except:
                    pass

            # Try API endpoints
            for call in api_calls:
                if 'medal' in call['url'].lower():
                    try:
                        response = requests.get(call['url'], timeout=10)
                        if response.status_code == 200:
                            api_data = response.json()
                            comp_data['medalists_api'] = api_data
                    except:
                        pass

        except Exception as e:
            print(f"[ERROR] Medalists: {e}")

        # Save competition data
        comp_file = self.output_dir / f"comp_{comp_slug}_data.json"
        with open(comp_file, 'w', encoding='utf-8') as f:
            json.dump(comp_data, f, indent=2)
        print(f"\n[SAVED] {comp_file.name}")

        return comp_data

    def scrape_profiles(self, driver):
        """Scrape athlete profiles"""
        print(f"\n{'='*70}")
        print("SCRAPING ATHLETE PROFILES")
        print(f"{'='*70}")

        url = f"{self.base_url}/profiles"
        print(f"\nURL: {url}")

        try:
            driver.get(url)
            time.sleep(5)

            # Extract API calls
            api_calls = self.extract_api_calls(driver)

            # Save page
            with open(self.output_dir / "profiles_page.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Try to get profiles from API
            for call in api_calls:
                if 'profile' in call['url'].lower() or 'athlete' in call['url'].lower():
                    print(f"\n[API] {call['url']}")
                    try:
                        response = requests.get(call['url'], timeout=10)
                        if response.status_code == 200:
                            api_data = response.json()
                            self.profiles = api_data

                            # Save
                            profiles_file = self.output_dir / "profiles_api.json"
                            with open(profiles_file, 'w', encoding='utf-8') as f:
                                json.dump(api_data, f, indent=2)
                            print(f"[SAVED] {profiles_file.name}")
                    except Exception as e:
                        print(f"[ERROR] {e}")

        except Exception as e:
            print(f"[ERROR] {e}")

    def scrape_country_statistics(self, driver):
        """Scrape country statistics"""
        print(f"\n{'='*70}")
        print("SCRAPING COUNTRY STATISTICS")
        print(f"{'='*70}")

        url = f"{self.base_url}/statistics/countries"
        print(f"\nURL: {url}")

        try:
            driver.get(url)
            time.sleep(5)

            # Extract API calls
            api_calls = self.extract_api_calls(driver)

            # Save page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            with open(self.output_dir / "country_stats_page.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Try to get stats from API
            for call in api_calls:
                if 'country' in call['url'].lower() or 'statistic' in call['url'].lower():
                    print(f"\n[API] {call['url']}")
                    try:
                        response = requests.get(call['url'], timeout=10)
                        if response.status_code == 200:
                            api_data = response.json()
                            self.country_stats = api_data

                            # Save
                            stats_file = self.output_dir / "country_stats_api.json"
                            with open(stats_file, 'w', encoding='utf-8') as f:
                                json.dump(api_data, f, indent=2)
                            print(f"[SAVED] {stats_file.name}")
                    except Exception as e:
                        print(f"[ERROR] {e}")

            # Also try to parse from HTML
            tables = soup.find_all('table')
            if tables:
                try:
                    df = pd.read_html(str(tables[0]))[0]
                    csv_file = self.output_dir / "country_stats.csv"
                    df.to_csv(csv_file, index=False, encoding='utf-8')
                    print(f"[SAVED] {csv_file.name}")
                except Exception as e:
                    print(f"[ERROR] Could not parse table: {e}")

        except Exception as e:
            print(f"[ERROR] {e}")

    def scrape_all(self):
        """Main scraping function"""
        print("="*70)
        print("WORLD TAEKWONDO API SCRAPER")
        print("="*70)

        driver = self.setup_driver_with_logging()

        try:
            # 1. Get competitions list
            competitions = self.scrape_competitions_list(driver)

            # 2. Get profiles
            self.scrape_profiles(driver)

            # 3. Get country statistics
            self.scrape_country_statistics(driver)

            # 4. Get detailed data for recent competitions
            print(f"\n{'='*70}")
            print("SCRAPING COMPETITION DETAILS")
            print(f"{'='*70}")

            if competitions:
                # Scrape first 10 competitions
                for idx, comp in enumerate(competitions[:10], 1):
                    if comp.get('slug'):
                        print(f"\n[{idx}/10]")
                        self.scrape_competition_details(driver, comp['slug'])
                        time.sleep(2)

        finally:
            driver.quit()

        print(f"\n{'='*70}")
        print("SCRAPING COMPLETE")
        print(f"{'='*70}")

    def save_summary(self):
        """Save summary of scraped data"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_competitions': len(self.competitions),
            'total_profiles': len(self.profiles) if isinstance(self.profiles, list) else 0,
            'competitions': self.competitions[:20],  # First 20
            'output_directory': str(self.output_dir.absolute())
        }

        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[SAVED] {summary_file.name}")

        # Save competitions list as CSV
        if self.competitions:
            try:
                df = pd.DataFrame(self.competitions)
                csv_file = self.output_dir / "competitions_list.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f"[SAVED] {csv_file.name}")
            except Exception as e:
                print(f"[ERROR] Could not create CSV: {e}")

def main():
    scraper = WorldTaekwondoAPIScraper()

    try:
        scraper.scrape_all()
        scraper.save_summary()

        print(f"\n[SUCCESS] Check {scraper.output_dir.absolute()} for all data")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        scraper.save_summary()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
