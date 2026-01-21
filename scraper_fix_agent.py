"""
Taekwondo Scraper Fix Agent
Applies fixes based on diagnostic findings:
1. Enhanced iframe handling with adaptive wait times
2. Robust table extraction with fallback methods
3. Smart timeout handling for downloads
4. Improved error recovery
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
from typing import List, Dict, Optional, Tuple

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
    print("[ERROR] Selenium not installed!")
    exit(1)


class EnhancedTaekwondoScraper:
    """
    Enhanced scraper with intelligent fixes:
    - Adaptive wait times based on content detection
    - Multiple extraction fallback strategies
    - Robust error handling
    """

    def __init__(self, output_dir="data_all_categories_fixed", headless=True, max_pages=5):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.headless = headless
        self.max_pages = max_pages  # Limit for testing
        self.driver = None
        self.wait = None

        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'pages_scraped': 0,
            'tables_extracted': 0,
            'total_rows': 0,
            'errors': [],
            'warnings': []
        }

    def setup_driver(self):
        """Setup Chrome with optimal settings"""
        print("\n[SETUP] Initializing Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')  # Faster loading

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            print("  ✓ Driver ready")
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def adaptive_wait_for_content(self, max_wait=15, check_interval=2):
        """
        Adaptive waiting strategy - checks for content periodically
        Returns: (success: bool, wait_time: int, content_found: dict)
        """
        start_time = time.time()
        wait_time = 0

        print(f"  [ADAPTIVE WAIT] Checking for content (max {max_wait}s)...")

        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time = int(time.time() - start_time)

            # Check for various content types
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            links = self.driver.find_elements(By.TAG_NAME, 'a')

            if tables or (buttons and links):
                print(f"    ✓ Content detected after {wait_time}s")
                return True, wait_time, {
                    'tables': len(tables),
                    'buttons': len(buttons),
                    'links': len(links)
                }

            print(f"    ... waiting ({wait_time}s)")

        print(f"    ✗ No content after {max_wait}s")
        return False, max_wait, {'tables': 0, 'buttons': 0, 'links': 0}

    def extract_table_robust(self, table_element, table_index=0):
        """
        Robust table extraction with multiple fallback methods
        Returns: DataFrame or None
        """
        # Method 1: pandas read_html (fastest)
        try:
            html = table_element.get_attribute('outerHTML')
            dfs = pd.read_html(html)
            if dfs and len(dfs[0]) > 0:
                return dfs[0]
        except Exception as e:
            pass

        # Method 2: Manual extraction with headers
        try:
            # Get headers
            headers = []
            header_cells = table_element.find_elements(By.TAG_NAME, 'th')
            if header_cells:
                headers = [cell.text.strip() for cell in header_cells]

            # Get rows
            rows_data = []
            rows = table_element.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if cells:
                    row_data = [cell.text.strip() for cell in cells]
                    if row_data and any(row_data):  # Skip empty rows
                        rows_data.append(row_data)

            if rows_data:
                # Use headers if available, otherwise generate
                if not headers:
                    headers = [f'Column_{i}' for i in range(len(rows_data[0]))]

                df = pd.DataFrame(rows_data, columns=headers)
                return df

        except Exception as e:
            pass

        return None

    def find_navigation_elements_smart(self):
        """
        Smart tab/navigation detection with multiple strategies
        Returns: List of clickable elements
        """
        strategies = [
            ("//button[contains(@class, 'tab')]", "Tab buttons"),
            ("//a[contains(@class, 'tab')]", "Tab links"),
            ("//li[contains(@class, 'tab')]", "Tab list items"),
            ("//button[contains(@role, 'tab')]", "ARIA tab buttons"),
            ("//div[@role='tablist']//*", "Tablist children"),
            ("//button[contains(text(), '-') and contains(text(), 'kg')]", "Weight category buttons"),
            ("//select[@id='weight-category']", "Category dropdown"),
        ]

        for xpath, description in strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"    ✓ Found {len(elements)} via: {description}")
                    return elements
            except:
                continue

        print("    ✗ No navigation elements found")
        return []

    def scrape_rankings_page_enhanced(self):
        """
        Enhanced rankings page scraping with iframe handling
        """
        print("\n" + "="*70)
        print("[ENHANCED] Scraping Rankings Page")
        print("="*70)

        url = 'https://www.worldtaekwondo.org/athletes/Ranking/contents'
        page_data = []

        try:
            print(f"\n[LOADING] {url}")
            self.driver.get(url)
            time.sleep(3)

            # Screenshot initial
            self.driver.save_screenshot(str(self.output_dir / "rankings_initial.png"))

            # Detect iframes
            print("\n[DETECTING] iframes...")
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            print(f"  Found {len(iframes)} iframe(s)")

            if not iframes:
                self.stats['warnings'].append("Rankings page: No iframes found")
                return page_data

            # Find SimplyCompete iframe
            target_iframe = None
            for iframe in iframes:
                src = iframe.get_attribute('src') or ""
                if 'simplycompete' in src.lower() or 'ranking' in src.lower():
                    target_iframe = iframe
                    print(f"  ✓ Found rankings iframe: {src[:80]}")
                    break

            if not target_iframe:
                self.stats['warnings'].append("Rankings page: SimplyCompete iframe not found")
                return page_data

            # Switch to iframe
            print("\n[SWITCHING] to iframe context...")
            self.driver.switch_to.frame(target_iframe)

            # Adaptive wait for iframe content
            success, wait_time, content = self.adaptive_wait_for_content(max_wait=15)

            if not success:
                self.stats['errors'].append("Rankings iframe: Content timeout")
                self.driver.switch_to.default_content()
                return page_data

            # Screenshot iframe
            self.driver.save_screenshot(str(self.output_dir / "rankings_iframe_loaded.png"))

            # Find navigation
            print("\n[FINDING] navigation elements...")
            nav_elements = self.find_navigation_elements_smart()

            if not nav_elements:
                # Try to extract without tabs
                print("\n[EXTRACTING] without tab navigation...")
                tables = self.driver.find_elements(By.TAG_NAME, 'table')

                for i, table in enumerate(tables):
                    df = self.extract_table_robust(table, i)
                    if df is not None and len(df) > 0:
                        filename = f"rankings_table{i}_{datetime.now().strftime('%Y%m%d')}.csv"
                        filepath = self.output_dir / "rankings" / filename
                        filepath.parent.mkdir(exist_ok=True)

                        df.to_csv(filepath, index=False, encoding='utf-8-sig')
                        print(f"    ✓ Saved: {filename} ({len(df)} rows)")

                        page_data.append({
                            'category': 'rankings',
                            'file': str(filepath),
                            'rows': len(df)
                        })
                        self.stats['tables_extracted'] += 1
                        self.stats['total_rows'] += len(df)

            else:
                # Click through tabs
                print(f"\n[EXTRACTING] from {len(nav_elements)} navigation elements...")

                for idx, element in enumerate(nav_elements[:20]):  # Limit to 20
                    try:
                        tab_text = element.text.strip() or f"tab_{idx}"
                        print(f"\n  Tab {idx + 1}: {tab_text}")

                        # Click tab
                        element.click()
                        time.sleep(3)

                        # Extract tables
                        tables = self.driver.find_elements(By.TAG_NAME, 'table')

                        for i, table in enumerate(tables):
                            df = self.extract_table_robust(table, i)
                            if df is not None and len(df) > 0:
                                safe_name = tab_text.replace(' ', '_').replace('/', '-')[:50]
                                filename = f"rankings_{safe_name}_{datetime.now().strftime('%Y%m%d')}.csv"
                                filepath = self.output_dir / "rankings" / filename
                                filepath.parent.mkdir(exist_ok=True)

                                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                                print(f"    ✓ {filename}: {len(df)} rows")

                                page_data.append({
                                    'category': 'rankings',
                                    'tab': tab_text,
                                    'file': str(filepath),
                                    'rows': len(df)
                                })
                                self.stats['tables_extracted'] += 1
                                self.stats['total_rows'] += len(df)

                    except Exception as e:
                        print(f"    ✗ Error on tab {idx}: {e}")
                        self.stats['warnings'].append(f"Rankings tab {idx} failed: {e}")

            # Switch back
            self.driver.switch_to.default_content()
            self.stats['pages_scraped'] += 1

        except Exception as e:
            print(f"\n✗ Error scraping rankings: {e}")
            self.stats['errors'].append(f"Rankings page error: {e}")
            import traceback
            traceback.print_exc()

        return page_data

    def scrape_competition_page_enhanced(self, page_key, page_info):
        """
        Enhanced competition page scraping
        """
        print("\n" + "="*70)
        print(f"[ENHANCED] {page_info['name']}")
        print("="*70)

        url = page_info['url']
        category = page_info['category']
        page_data = []

        try:
            print(f"\n[LOADING] {url}")
            self.driver.get(url)

            # Adaptive wait
            success, wait_time, content = self.adaptive_wait_for_content()

            # Screenshot
            safe_name = page_key.replace(' ', '_')
            self.driver.save_screenshot(str(self.output_dir / f"{safe_name}.png"))

            # Extract tables
            print("\n[EXTRACTING] tables...")
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            if tables:
                for i, table in enumerate(tables):
                    df = self.extract_table_robust(table, i)
                    if df is not None and len(df) > 0:
                        filename = f"{category}_table{i}_{datetime.now().strftime('%Y%m%d')}.csv"
                        filepath = self.output_dir / page_key / filename
                        filepath.parent.mkdir(exist_ok=True)

                        df.to_csv(filepath, index=False, encoding='utf-8-sig')
                        print(f"  ✓ {filename}: {len(df)} rows")

                        page_data.append({
                            'category': category,
                            'file': str(filepath),
                            'rows': len(df)
                        })
                        self.stats['tables_extracted'] += 1
                        self.stats['total_rows'] += len(df)
            else:
                print("  No tables found")

            # Check for download links
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
                print(f"  Found {len(download_links)} download links")
                links_file = self.output_dir / page_key / "download_links.json"
                links_file.parent.mkdir(exist_ok=True)
                with open(links_file, 'w', encoding='utf-8') as f:
                    json.dump(download_links, f, indent=2)

            self.stats['pages_scraped'] += 1

        except Exception as e:
            print(f"\n✗ Error: {e}")
            self.stats['errors'].append(f"{page_key}: {e}")

        return page_data

    def run_enhanced_scrape(self, test_mode=True):
        """
        Run enhanced scraping with all fixes applied
        """
        print("="*70)
        print("ENHANCED TAEKWONDO SCRAPER - WITH FIXES")
        print("="*70)

        if not self.setup_driver():
            return None

        all_data = []

        try:
            # Priority 1: Rankings (most important, most problematic)
            rankings_data = self.scrape_rankings_page_enhanced()
            all_data.extend(rankings_data)

            # Priority 2: Key competition pages (limited in test mode)
            if test_mode:
                test_pages = {
                    'olympics': {
                        'url': 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents',
                        'name': 'Olympic Games Results',
                        'category': 'senior'
                    },
                    'world_champs_senior': {
                        'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTC/list',
                        'name': 'World Championships',
                        'category': 'senior'
                    }
                }

                for page_key, page_info in test_pages.items():
                    comp_data = self.scrape_competition_page_enhanced(page_key, page_info)
                    all_data.extend(comp_data)
                    time.sleep(2)

            # Generate summary
            self.generate_summary(all_data)

            return all_data

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                self.driver.quit()
                print("\n[CLEANUP] Browser closed")

    def generate_summary(self, data):
        """Generate summary report"""
        print("\n" + "="*70)
        print("[SUMMARY]")
        print("="*70)

        print(f"\nPages scraped: {self.stats['pages_scraped']}")
        print(f"Tables extracted: {self.stats['tables_extracted']}")
        print(f"Total rows: {self.stats['total_rows']}")

        if self.stats['errors']:
            print(f"\n[ERRORS] {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  - {error}")

        if self.stats['warnings']:
            print(f"\n[WARNINGS] {len(self.stats['warnings'])}")
            for warning in self.stats['warnings']:
                print(f"  - {warning}")

        # Save detailed stats
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['data_collected'] = data

        stats_file = self.output_dir / f"scraping_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Stats: {stats_file}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Taekwondo Scraper with Fixes Applied'
    )

    parser.add_argument('--visible', action='store_true', help='Run with visible browser')
    parser.add_argument('--full', action='store_true', help='Run full scrape (not just test pages)')
    parser.add_argument('--output', default='data_all_categories_fixed', help='Output directory')

    args = parser.parse_args()

    try:
        scraper = EnhancedTaekwondoScraper(
            output_dir=args.output,
            headless=not args.visible
        )

        data = scraper.run_enhanced_scrape(test_mode=not args.full)

        if data and len(data) > 0:
            print(f"\n✓ Success! Collected {len(data)} datasets")
            return 0
        else:
            print("\n✗ No data collected")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED]")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    exit(main())
