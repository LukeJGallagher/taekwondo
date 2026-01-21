"""
Complete Taekwondo Web Scraping Agent
Autonomous agent that combines all fixes and enhancements:
1. Enhanced iframe handling with adaptive waits
2. Robust table extraction with fallback methods
3. Smart timeout handling
4. Comprehensive data collection across all categories
5. Detailed logging and progress tracking
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium not installed! Run: pip install selenium")
    exit(1)


class CompleteTaekwondoScraperAgent:
    """
    Autonomous web scraping agent with all enhancements
    """

    # All competition categories to scrape
    COMPETITION_CATEGORIES = {
        'rankings': {
            'url': 'https://www.worldtaekwondo.org/athletes/Ranking/contents',
            'name': 'World Rankings',
            'priority': 1,
            'has_iframe': True
        },
        'olympics': {
            'url': 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents',
            'name': 'Olympic Games',
            'priority': 2,
            'has_iframe': False
        },
        'world_champs_senior': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTC/list',
            'name': 'World Championships',
            'priority': 3,
            'has_iframe': False
        },
        'grand_prix': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WTGPS/list',
            'name': 'Grand Prix',
            'priority': 4,
            'has_iframe': False
        },
        'grand_slam': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGS/WGS_WTGSC/list',
            'name': 'Grand Slam',
            'priority': 5,
            'has_iframe': False
        }
    }

    def __init__(self, output_dir="data_scraped", headless=True, max_pages=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.headless = headless
        self.max_pages = max_pages
        self.driver = None
        self.wait = None

        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'categories_scraped': 0,
            'tables_extracted': 0,
            'total_rows': 0,
            'download_links_found': 0,
            'errors': [],
            'warnings': []
        }

        # Create category folders
        for category in self.COMPETITION_CATEGORIES.keys():
            (self.output_dir / category).mkdir(exist_ok=True)

    def setup_driver(self):
        """Setup Chrome with optimal configuration"""
        print("\n[AGENT] Initializing Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
            print("  Mode: Headless")
        else:
            print("  Mode: Visible")

        # Performance optimizations
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            print("  ✓ Driver ready")
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.stats['errors'].append(f"Driver setup: {e}")
            return False

    def adaptive_wait(self, max_wait=15, check_interval=2):
        """Wait for content with periodic checks"""
        start = time.time()
        wait_time = 0

        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time = int(time.time() - start)

            # Check for content
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            if tables:
                return True, wait_time

        return False, max_wait

    def extract_table_smart(self, table_element):
        """Extract table with multiple fallback methods"""
        # Method 1: pandas read_html
        try:
            html = table_element.get_attribute('outerHTML')
            from io import StringIO
            dfs = pd.read_html(StringIO(html))
            if dfs and len(dfs[0]) > 0:
                return dfs[0]
        except:
            pass

        # Method 2: Manual extraction
        try:
            headers = []
            header_cells = table_element.find_elements(By.TAG_NAME, 'th')
            if header_cells:
                headers = [cell.text.strip() for cell in header_cells]

            rows_data = []
            rows = table_element.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if cells:
                    row_data = [cell.text.strip() for cell in cells]
                    if any(row_data):
                        rows_data.append(row_data)

            if rows_data:
                if not headers:
                    headers = [f'Column_{i}' for i in range(len(rows_data[0]))]
                return pd.DataFrame(rows_data, columns=headers)
        except:
            pass

        return None

    def scrape_rankings_iframe(self):
        """Specialized scraper for rankings iframe"""
        print("\n" + "="*70)
        print("[SCRAPING] World Rankings (iframe)")
        print("="*70)

        url = self.COMPETITION_CATEGORIES['rankings']['url']
        data_collected = []

        try:
            print(f"\n[LOADING] {url}")
            self.driver.get(url)
            time.sleep(3)

            # Find iframe
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            print(f"  Found {len(iframes)} iframes")

            target_iframe = None
            for iframe in iframes:
                src = iframe.get_attribute('src') or ""
                if 'simplycompete' in src.lower() or 'ranking' in src.lower():
                    target_iframe = iframe
                    print(f"  ✓ Rankings iframe: {src[:80]}...")
                    break

            if not target_iframe:
                self.stats['warnings'].append("Rankings: iframe not found")
                return data_collected

            # Switch to iframe
            self.driver.switch_to.frame(target_iframe)
            print("\n  [WAITING] for iframe content...")

            success, wait_time = self.adaptive_wait(max_wait=15)
            print(f"  Content ready after {wait_time}s")

            # Extract tables
            print("\n  [EXTRACTING] tables from iframe...")
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            for i, table in enumerate(tables):
                df = self.extract_table_smart(table)
                if df is not None and len(df) > 1:  # More than just header
                    filename = f"rankings_table{i}_{datetime.now().strftime('%Y%m%d')}.csv"
                    filepath = self.output_dir / "rankings" / filename

                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                    print(f"    ✓ {filename}: {len(df)} rows × {len(df.columns)} cols")

                    data_collected.append({
                        'category': 'rankings',
                        'file': str(filepath),
                        'rows': len(df),
                        'columns': len(df.columns)
                    })

                    self.stats['tables_extracted'] += 1
                    self.stats['total_rows'] += len(df)

            # Switch back
            self.driver.switch_to.default_content()
            self.stats['categories_scraped'] += 1

        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            self.stats['errors'].append(f"Rankings: {e}")
            if self.driver:
                self.driver.switch_to.default_content()

        return data_collected

    def scrape_competition_page(self, category_key, category_info):
        """Scrape standard competition page"""
        print("\n" + "="*70)
        print(f"[SCRAPING] {category_info['name']}")
        print("="*70)

        url = category_info['url']
        data_collected = []

        try:
            print(f"\n[LOADING] {url}")
            self.driver.get(url)

            success, wait_time = self.adaptive_wait()
            print(f"  Content ready after {wait_time}s")

            # Extract tables
            print("\n  [EXTRACTING] tables...")
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            if tables:
                for i, table in enumerate(tables):
                    df = self.extract_table_smart(table)
                    if df is not None and len(df) > 1:
                        filename = f"{category_key}_table{i}_{datetime.now().strftime('%Y%m%d')}.csv"
                        filepath = self.output_dir / category_key / filename

                        df.to_csv(filepath, index=False, encoding='utf-8-sig')
                        print(f"    ✓ {filename}: {len(df)} rows")

                        data_collected.append({
                            'category': category_key,
                            'file': str(filepath),
                            'rows': len(df)
                        })

                        self.stats['tables_extracted'] += 1
                        self.stats['total_rows'] += len(df)
            else:
                print("    No tables found")

            # Find download links
            print("\n  [FINDING] download links...")
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            download_links = []

            for link in links:
                href = link.get_attribute('href')
                if href and any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                    download_links.append({
                        'url': href,
                        'text': link.text.strip()
                    })

            if download_links:
                print(f"    ✓ Found {len(download_links)} download links")
                links_file = self.output_dir / category_key / "download_links.json"
                with open(links_file, 'w', encoding='utf-8') as f:
                    json.dump(download_links, f, indent=2)

                self.stats['download_links_found'] += len(download_links)

            self.stats['categories_scraped'] += 1

        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            self.stats['errors'].append(f"{category_key}: {e}")

        return data_collected

    def run_autonomous_scrape(self):
        """Main autonomous scraping operation"""
        print("="*70)
        print("TAEKWONDO WEB SCRAPING AGENT")
        print("Autonomous Data Collection System")
        print("="*70)

        if not self.setup_driver():
            return None

        all_data = []

        try:
            # Sort categories by priority
            sorted_categories = sorted(
                self.COMPETITION_CATEGORIES.items(),
                key=lambda x: x[1]['priority']
            )

            # Limit categories if max_pages set
            if self.max_pages:
                sorted_categories = sorted_categories[:self.max_pages]

            # Scrape each category
            for category_key, category_info in sorted_categories:
                print(f"\n[PROGRESS] Category {category_info['priority']} of {len(sorted_categories)}")

                if category_info.get('has_iframe'):
                    data = self.scrape_rankings_iframe()
                else:
                    data = self.scrape_competition_page(category_key, category_info)

                all_data.extend(data)
                time.sleep(2)  # Be nice to the server

            # Generate report
            self.generate_report(all_data)

            return all_data

        except KeyboardInterrupt:
            print("\n\n[INTERRUPTED] User stopped scraping")
            self.generate_report(all_data)
            return all_data

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.generate_report(all_data)
            return all_data

        finally:
            if self.driver:
                self.driver.quit()
                print("\n[CLEANUP] Browser closed")

    def generate_report(self, data):
        """Generate comprehensive scraping report"""
        print("\n" + "="*70)
        print("[SCRAPING REPORT]")
        print("="*70)

        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds() / 60

        print(f"\nRuntime: {elapsed:.1f} minutes")
        print(f"Categories scraped: {self.stats['categories_scraped']}")
        print(f"Tables extracted: {self.stats['tables_extracted']}")
        print(f"Total data rows: {self.stats['total_rows']}")
        print(f"Download links found: {self.stats['download_links_found']}")

        if self.stats['errors']:
            print(f"\n[ERRORS] {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")

        if self.stats['warnings']:
            print(f"\n[WARNINGS] {len(self.stats['warnings'])}")
            for warning in self.stats['warnings'][:5]:
                print(f"  - {warning}")

        # Save detailed report
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['runtime_minutes'] = elapsed
        self.stats['data_collected'] = data

        report_file = self.output_dir / f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Detailed report: {report_file}")
        print(f"[OUTPUT] Data directory: {self.output_dir.absolute()}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Autonomous Taekwondo Web Scraping Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Autonomous Features:
  ✓ Adaptive wait times based on content detection
  ✓ Multiple extraction fallback methods
  ✓ Smart iframe handling
  ✓ Automatic error recovery
  ✓ Comprehensive logging and reporting

Examples:
  # Run with visible browser (debugging)
  python scraper_agent_complete.py --visible

  # Run headless (production)
  python scraper_agent_complete.py

  # Limit to top 3 priority categories
  python scraper_agent_complete.py --max-pages 3
        """
    )

    parser.add_argument('--visible', action='store_true',
                        help='Run with visible browser')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Limit number of categories to scrape')
    parser.add_argument('--output', default='data_scraped',
                        help='Output directory (default: data_scraped)')

    args = parser.parse_args()

    try:
        agent = CompleteTaekwondoScraperAgent(
            output_dir=args.output,
            headless=not args.visible,
            max_pages=args.max_pages
        )

        data = agent.run_autonomous_scrape()

        if data and len(data) > 0:
            print(f"\n✓ SUCCESS! Collected {len(data)} datasets")
            print(f"  Total rows: {sum(d['rows'] for d in data)}")
            return 0
        else:
            print("\n⚠ No data collected")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED]")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
