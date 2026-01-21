"""
Specialized Scraper for High-Value World Taekwondo Pages
Targets specific pages with tabbed data:
1. Rankings (with tabs for different categories)
2. Olympic Results (historical tabs)
3. Records & Stats (various statistics)
"""

import os
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict

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
    print("Install with: pip install selenium webdriver-manager")
    exit(1)


class SpecificPagesScraper:
    """Scrape specific high-value pages with tabbed content"""

    def __init__(self, output_dir="data_detailed", headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        (self.output_dir / "olympics").mkdir(exist_ok=True)
        (self.output_dir / "records").mkdir(exist_ok=True)
        (self.output_dir / "screenshots").mkdir(exist_ok=True)

        # Setup Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
        except Exception as e:
            print(f"[ERROR] Error starting Chrome: {e}")
            print("\nTry: pip install webdriver-manager")
            raise

        self.data_collected = {
            'rankings': [],
            'olympics': [],
            'records': []
        }

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def wait_for_load(self, timeout=30):
        """Wait for page to finish loading"""
        time.sleep(3)  # Initial wait

        # Wait for loading indicators to disappear
        try:
            self.wait.until_not(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Loading')]"))
            )
        except:
            pass  # Loading might already be gone

        # Wait for body to be present
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Extra wait for JavaScript

    def find_and_click_tabs(self):
        """Find all tabs on page and return them"""
        tabs = []

        # Try different tab selectors
        tab_selectors = [
            "//button[contains(@class, 'tab')]",
            "//a[contains(@class, 'tab')]",
            "//li[contains(@class, 'tab')]",
            "//div[contains(@class, 'tab-item')]",
            "//ul[@role='tablist']//button",
            "//ul[@role='tablist']//a",
        ]

        for selector in tab_selectors:
            try:
                found_tabs = self.driver.find_elements(By.XPATH, selector)
                if found_tabs:
                    print(f"  Found {len(found_tabs)} tabs using: {selector}")
                    tabs.extend(found_tabs)
                    break
            except:
                continue

        return tabs

    def extract_tables(self):
        """Extract all tables from current page"""
        tables_data = []

        try:
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            print(f"  Found {len(tables)} tables")

            for i, table in enumerate(tables):
                try:
                    # Get table HTML
                    table_html = table.get_attribute('outerHTML')

                    # Try to parse with pandas
                    try:
                        dfs = pd.read_html(table_html)
                        if dfs:
                            tables_data.append({
                                'table_index': i,
                                'dataframe': dfs[0],
                                'html': table_html
                            })
                            print(f"    Table {i}: {dfs[0].shape[0]} rows x {dfs[0].shape[1]} cols")
                    except:
                        # Manual extraction if pandas fails
                        headers = []
                        rows_data = []

                        # Get headers
                        header_cells = table.find_elements(By.TAG_NAME, 'th')
                        if header_cells:
                            headers = [cell.text.strip() for cell in header_cells]

                        # Get rows
                        rows = table.find_elements(By.TAG_NAME, 'tr')
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            if cells:
                                row_data = [cell.text.strip() for cell in cells]
                                rows_data.append(row_data)

                        if rows_data:
                            df = pd.DataFrame(rows_data, columns=headers if headers else None)
                            tables_data.append({
                                'table_index': i,
                                'dataframe': df,
                                'html': table_html
                            })
                            print(f"    Table {i}: {len(rows_data)} rows")

                except Exception as e:
                    print(f"    Error extracting table {i}: {e}")
                    continue

        except Exception as e:
            print(f"  Error finding tables: {e}")

        return tables_data

    def scrape_rankings_page(self):
        """Scrape rankings page with all tabs"""
        print("\n[1] SCRAPING RANKINGS PAGE")
        print("=" * 70)

        url = "https://www.worldtaekwondo.org/athletes/Ranking/contents"
        self.driver.get(url)
        self.wait_for_load()

        # Screenshot
        screenshot_path = self.output_dir / "screenshots" / f"rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_path))
        print(f"[SCREENSHOT] {screenshot_path}")

        # Look for downloadable files
        download_links = []
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            text = link.text.strip()
            if href and any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                download_links.append({'url': href, 'text': text})
                print(f"  [DOWNLOAD] Found file: {text} -> {href}")

        # Look for iframe (SimplyCompete)
        iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"\n  Found {len(iframes)} iframes")

        for i, iframe in enumerate(iframes):
            iframe_src = iframe.get_attribute('src')
            print(f"  iframe {i}: {iframe_src}")

            if 'simplycompete' in iframe_src or 'ranking' in iframe_src.lower():
                print(f"\n  Switching to rankings iframe...")
                self.driver.switch_to.frame(iframe)
                time.sleep(5)  # Wait for iframe content

                # Find tabs in iframe
                tabs = self.find_and_click_tabs()

                if tabs:
                    print(f"  Found {len(tabs)} tabs in iframe")

                    for tab_idx, tab in enumerate(tabs[:10]):  # Limit to first 10 tabs
                        try:
                            tab_text = tab.text.strip()
                            print(f"\n  Clicking tab {tab_idx + 1}: {tab_text}")

                            tab.click()
                            time.sleep(3)

                            # Extract tables from this tab
                            tables = self.extract_tables()

                            # Save each table
                            for table_data in tables:
                                df = table_data['dataframe']
                                filename = f"rankings_tab{tab_idx}_{tab_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
                                filepath = self.output_dir / "rankings" / filename
                                df.to_csv(filepath, index=False)
                                print(f"    [SAVED] {filename}")

                                self.data_collected['rankings'].append({
                                    'tab': tab_text,
                                    'file': str(filepath),
                                    'rows': len(df)
                                })

                        except Exception as e:
                            print(f"    Error on tab {tab_idx}: {e}")
                            continue

                # Switch back to main page
                self.driver.switch_to.default_content()
                break

        # Save download links
        if download_links:
            links_file = self.output_dir / "rankings" / "downloadable_files.json"
            with open(links_file, 'w') as f:
                json.dump(download_links, f, indent=2)
            print(f"\n[SAVED] Download links: {links_file}")

    def scrape_olympic_results(self):
        """Scrape Olympic results page"""
        print("\n[2] SCRAPING OLYMPIC RESULTS PAGE")
        print("=" * 70)

        url = "https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents"
        self.driver.get(url)
        self.wait_for_load()

        # Screenshot
        screenshot_path = self.output_dir / "screenshots" / f"olympics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_path))
        print(f"[SCREENSHOT] {screenshot_path}")

        # Find tabs for different Olympics
        tabs = self.find_and_click_tabs()

        if tabs:
            print(f"  Found {len(tabs)} Olympic tabs")

            for tab_idx, tab in enumerate(tabs):
                try:
                    tab_text = tab.text.strip()
                    print(f"\n  Tab {tab_idx + 1}: {tab_text}")

                    tab.click()
                    time.sleep(3)

                    # Extract tables
                    tables = self.extract_tables()

                    for table_data in tables:
                        df = table_data['dataframe']
                        filename = f"olympic_{tab_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
                        filepath = self.output_dir / "olympics" / filename
                        df.to_csv(filepath, index=False)
                        print(f"    💾 Saved: {filename}")

                        self.data_collected['olympics'].append({
                            'olympic': tab_text,
                            'file': str(filepath),
                            'rows': len(df)
                        })

                except Exception as e:
                    print(f"    Error on tab {tab_idx}: {e}")
                    continue
        else:
            # No tabs found, just extract all tables on page
            print("  No tabs found, extracting all tables...")
            tables = self.extract_tables()

            for table_data in tables:
                df = table_data['dataframe']
                filename = f"olympic_all_{datetime.now().strftime('%Y%m%d')}.csv"
                filepath = self.output_dir / "olympics" / filename
                df.to_csv(filepath, index=False)
                print(f"  💾 Saved: {filename}")

    def scrape_records_stats(self):
        """Scrape records and statistics page"""
        print("\n[3] SCRAPING RECORDS & STATS PAGE")
        print("=" * 70)

        url = "https://www.worldtaekwondo.org/competitions/RECORD&STATS/contents"
        self.driver.get(url)
        self.wait_for_load()

        # Screenshot
        screenshot_path = self.output_dir / "screenshots" / f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_path))
        print(f"[SCREENSHOT] {screenshot_path}")

        # Find tabs
        tabs = self.find_and_click_tabs()

        if tabs:
            print(f"  Found {len(tabs)} tabs")

            for tab_idx, tab in enumerate(tabs):
                try:
                    tab_text = tab.text.strip()
                    print(f"\n  Tab {tab_idx + 1}: {tab_text}")

                    tab.click()
                    time.sleep(3)

                    # Extract tables
                    tables = self.extract_tables()

                    for table_data in tables:
                        df = table_data['dataframe']
                        filename = f"records_{tab_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
                        filepath = self.output_dir / "records" / filename
                        df.to_csv(filepath, index=False)
                        print(f"    💾 Saved: {filename}")

                        self.data_collected['records'].append({
                            'category': tab_text,
                            'file': str(filepath),
                            'rows': len(df)
                        })

                except Exception as e:
                    print(f"    Error on tab {tab_idx}: {e}")
                    continue
        else:
            # No tabs, extract all tables
            print("  No tabs found, extracting all tables...")
            tables = self.extract_tables()

            for table_data in tables:
                df = table_data['dataframe']
                filename = f"records_all_{datetime.now().strftime('%Y%m%d')}.csv"
                filepath = self.output_dir / "records" / filename
                df.to_csv(filepath, index=False)
                print(f"  💾 Saved: {filename}")

    def generate_summary(self):
        """Generate summary of collected data"""
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)

        print(f"\n[RANKINGS DATA]")
        print(f"   Files collected: {len(self.data_collected['rankings'])}")
        for item in self.data_collected['rankings']:
            print(f"   - {item['tab']}: {item['rows']} rows")

        print(f"\n[OLYMPIC RESULTS]")
        print(f"   Files collected: {len(self.data_collected['olympics'])}")
        for item in self.data_collected['olympics']:
            print(f"   - {item['olympic']}: {item['rows']} rows")

        print(f"\n[RECORDS & STATS]")
        print(f"   Files collected: {len(self.data_collected['records'])}")
        for item in self.data_collected['records']:
            print(f"   - {item['category']}: {item['rows']} rows")

        print(f"\n[OUTPUT] Directory: {self.output_dir.absolute()}")
        print(f"[SCREENSHOTS] {self.output_dir / 'screenshots'}")

        # Save summary
        summary_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.data_collected, f, indent=2)
        print(f"\n[SAVED] Summary: {summary_file}")

        print("\n" + "=" * 70)

    def run_all(self):
        """Run all scrapers"""
        print("=" * 70)
        print(" " * 15 + "SPECIFIC PAGES SCRAPER")
        print(" " * 10 + "Rankings - Olympics - Records & Stats")
        print("=" * 70)

        try:
            # Scrape each page
            self.scrape_rankings_page()
            time.sleep(2)

            self.scrape_olympic_results()
            time.sleep(2)

            self.scrape_records_stats()

            # Generate summary
            self.generate_summary()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Scrape specific World Taekwondo pages with tabbed data')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--output', default='data_detailed', help='Output directory')

    args = parser.parse_args()

    if not SELENIUM_AVAILABLE:
        print("[ERROR] Selenium is required for this scraper")
        print("Install: pip install selenium webdriver-manager")
        return

    try:
        scraper = SpecificPagesScraper(output_dir=args.output, headless=args.headless)
        scraper.run_all()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
