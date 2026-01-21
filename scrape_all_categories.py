"""
COMPREHENSIVE World Taekwondo Scraper - ALL Categories
Scrapes ALL rankings, results, and statistics for:
- Senior
- Junior
- U-21
- Cadet
- Children
- Youth Olympics
- Olympic Games
- Records & Stats
"""

# Add UTF-8 encoding support for Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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


class ComprehensiveTaekwondoScraper:
    """Scrape ALL World Taekwondo data across all age categories"""

    # ALL PAGES TO SCRAPE - COMPREHENSIVE LIST
    PAGES_TO_SCRAPE = {
        # Rankings
        'rankings': {
            'url': 'https://www.worldtaekwondo.org/athletes/Ranking/contents',
            'name': 'Senior Rankings',
            'category': 'senior'
        },

        # Olympic & Paralympic
        'olympics': {
            'url': 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents',
            'name': 'Olympic Games Results',
            'category': 'senior'
        },
        'paralympics': {
            'url': 'https://www.worldtaekwondo.org/competitions/OP/OP_PG/list',
            'name': 'Paralympic Games',
            'category': 'para'
        },
        'youth_olympics': {
            'url': 'https://www.worldtaekwondo.org/competitions/OP/OP_YOG/list',
            'name': 'Youth Olympic Games',
            'category': 'youth'
        },

        # World Championships - ALL Age Categories
        'world_champs_senior': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTC/list',
            'name': 'World Taekwondo Championships (Senior)',
            'category': 'senior'
        },
        'world_champs_para': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WPTC/list',
            'name': 'World Para Taekwondo Championships',
            'category': 'para'
        },
        'world_champs_u21': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTUC/list',
            'name': 'World U-21 Championships',
            'category': 'u21'
        },
        'world_champs_junior': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTJC/list',
            'name': 'World Junior Championships',
            'category': 'junior'
        },
        'world_champs_cadet': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTCC/list',
            'name': 'World Cadet Championships',
            'category': 'cadet'
        },
        'world_champs_children': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTCCS/list',
            'name': 'World Children Championships',
            'category': 'children'
        },
        'world_champs_veterans': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTVC/list',
            'name': 'World Veteran Championships',
            'category': 'veteran'
        },

        # Grand Prix Series
        'grand_prix': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WTGPS/list',
            'name': 'Grand Prix Series',
            'category': 'senior'
        },
        'grand_prix_para': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WPTGPS/list',
            'name': 'Para Grand Prix Series',
            'category': 'para'
        },
        'grand_prix_final': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WTGPF/list',
            'name': 'Grand Prix Final',
            'category': 'senior'
        },
        'grand_prix_challenge': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WTGPC/list',
            'name': 'Grand Prix Challenge',
            'category': 'senior'
        },

        # Grand Slam
        'grand_slam': {
            'url': 'https://www.worldtaekwondo.org/competitions/WGS/WGS_WTGSC/list',
            'name': 'Grand Slam Champions Series',
            'category': 'senior'
        },

        # World Cup
        'world_cup_team': {
            'url': 'https://www.worldtaekwondo.org/competitions/WTCC/WTCC_WTCC/list',
            'name': 'World Cup Team Championships',
            'category': 'senior'
        },

        # Poomsae
        'poomsae': {
            'url': 'https://www.worldtaekwondo.org/competitions/WP/WP_WTPC/list',
            'name': 'World Poomsae Championships',
            'category': 'poomsae'
        },
        'poomsae_para': {
            'url': 'https://www.worldtaekwondo.org/competitions/WP/WP_WPTPC/list',
            'name': 'World Para Poomsae Championships',
            'category': 'poomsae_para'
        },

        # Special Events
        'beach_championships': {
            'url': 'https://www.worldtaekwondo.org/competitions/WTSE/WTSE_WTBC/list',
            'name': 'Beach Championships',
            'category': 'beach'
        },
        'womens_open': {
            'url': 'https://www.worldtaekwondo.org/competitions/WTSE/WTSE_WTWOC/list',
            'name': 'Womens Open Championships',
            'category': 'women'
        },

        # Records & Stats
        'records': {
            'url': 'https://www.worldtaekwondo.org/competitions/RECORD&STATS/contents',
            'name': 'Records & Statistics',
            'category': 'all'
        }
    }

    def __init__(self, output_dir="data_all_categories", headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create category subdirectories
        for page_key in self.PAGES_TO_SCRAPE.keys():
            (self.output_dir / page_key).mkdir(exist_ok=True)

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

        self.data_collected = {}
        for page_key in self.PAGES_TO_SCRAPE.keys():
            self.data_collected[page_key] = []

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def wait_for_load(self, timeout=30):
        """Wait for page to finish loading"""
        time.sleep(3)
        try:
            self.wait.until_not(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Loading')]")))
        except:
            pass
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

    def find_tabs(self):
        """Find all tabs on current page"""
        tabs = []
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

            for i, table in enumerate(tables):
                try:
                    table_html = table.get_attribute('outerHTML')
                    try:
                        dfs = pd.read_html(table_html)
                        if dfs:
                            tables_data.append({
                                'table_index': i,
                                'dataframe': dfs[0],
                                'html': table_html
                            })
                    except:
                        headers = []
                        rows_data = []

                        header_cells = table.find_elements(By.TAG_NAME, 'th')
                        if header_cells:
                            headers = [cell.text.strip() for cell in header_cells]

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

                except Exception as e:
                    continue

        except Exception as e:
            pass

        return tables_data

    def scrape_page(self, page_key: str, page_info: Dict):
        """Scrape a single page with all its tabs"""
        print(f"\n[SCRAPING] {page_info['name']}")
        print("=" * 70)

        url = page_info['url']
        category = page_info['category']

        self.driver.get(url)
        self.wait_for_load()

        # Screenshot
        screenshot_path = self.output_dir / "screenshots" / f"{page_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_path))
        print(f"[SCREENSHOT] {screenshot_path.name}")

        # Look for downloadable files
        download_links = []
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            text = link.text.strip()
            if href and any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                download_links.append({'url': href, 'text': text})
                print(f"  [FILE] {text}")

        # Save download links
        if download_links:
            links_file = self.output_dir / page_key / "downloadable_files.json"
            with open(links_file, 'w', encoding='utf-8') as f:
                json.dump(download_links, f, indent=2)

        # Look for iframes (for rankings page)
        iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
        if iframes:
            print(f"  [IFRAMES] Found {len(iframes)}")

            for i, iframe in enumerate(iframes):
                iframe_src = iframe.get_attribute('src')
                if 'simplycompete' in iframe_src or 'ranking' in iframe_src.lower():
                    print(f"  [IFRAME] Switching to rankings iframe")
                    self.driver.switch_to.frame(iframe)
                    time.sleep(5)

                    tabs = self.find_tabs()
                    if tabs:
                        print(f"  [TABS] Found {len(tabs)} tabs in iframe")
                        self.extract_from_tabs(tabs, page_key, category)

                    self.driver.switch_to.default_content()
                    break

        # Look for tabs on main page
        tabs = self.find_tabs()
        if tabs and not iframes:
            print(f"  [TABS] Found {len(tabs)} tabs")
            self.extract_from_tabs(tabs, page_key, category)

        # If no tabs, extract all tables
        if not tabs:
            print(f"  [TABLES] Extracting all tables")
            tables = self.extract_tables()
            self.save_tables(tables, page_key, category, "all")

    def extract_from_tabs(self, tabs, page_key, category):
        """Extract data from all tabs"""
        for tab_idx, tab in enumerate(tabs[:20]):  # Limit to 20 tabs
            try:
                tab_text = tab.text.strip()
                if not tab_text:
                    tab_text = f"tab_{tab_idx}"

                print(f"  [TAB {tab_idx + 1}] {tab_text}")

                tab.click()
                time.sleep(3)

                tables = self.extract_tables()
                self.save_tables(tables, page_key, category, tab_text)

            except Exception as e:
                print(f"    [ERROR] Tab {tab_idx}: {e}")
                continue

    def save_tables(self, tables, page_key, category, tab_name):
        """Save extracted tables"""
        for table_data in tables:
            df = table_data['dataframe']
            if len(df) == 0:
                continue

            filename = f"{category}_{tab_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = self.output_dir / page_key / filename

            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"    [SAVED] {filename} ({len(df)} rows)")

            self.data_collected[page_key].append({
                'category': category,
                'tab': tab_name,
                'file': str(filepath),
                'rows': len(df),
                'columns': len(df.columns)
            })

    def generate_summary(self):
        """Generate comprehensive summary"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE SCRAPING SUMMARY")
        print("=" * 70)

        total_files = 0
        total_rows = 0

        for page_key, page_info in self.PAGES_TO_SCRAPE.items():
            data = self.data_collected[page_key]
            if data:
                print(f"\n[{page_info['name'].upper()}]")
                print(f"  Files: {len(data)}")
                for item in data:
                    print(f"    - {item['tab']}: {item['rows']} rows x {item['columns']} cols")
                    total_rows += item['rows']
                total_files += len(data)

        print(f"\n[TOTAL]")
        print(f"  Files collected: {total_files}")
        print(f"  Total rows: {total_rows}")
        print(f"  Output directory: {self.output_dir.absolute()}")

        # Save summary
        summary_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scrape_date': datetime.now().isoformat(),
                'total_files': total_files,
                'total_rows': total_rows,
                'pages': self.PAGES_TO_SCRAPE,
                'data_collected': self.data_collected
            }, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Summary: {summary_file.name}")
        print("=" * 70)

    def run_all(self):
        """Run comprehensive scraping of all categories"""
        print("=" * 70)
        print("COMPREHENSIVE TAEKWONDO DATA SCRAPER")
        print("ALL Age Categories: Senior | Junior | U-21 | Cadet | Children")
        print("=" * 70)

        try:
            for page_key, page_info in self.PAGES_TO_SCRAPE.items():
                self.scrape_page(page_key, page_info)
                time.sleep(3)  # Be nice to the server

            self.generate_summary()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive Taekwondo Scraper - ALL Categories')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (default: True)', default=True)
    parser.add_argument('--visible', action='store_true', help='Run with visible browser')
    parser.add_argument('--output', default='data_all_categories', help='Output directory')

    args = parser.parse_args()

    headless = args.headless and not args.visible

    if not SELENIUM_AVAILABLE:
        print("[ERROR] Selenium is required")
        print("Install: pip install selenium webdriver-manager")
        return

    try:
        scraper = ComprehensiveTaekwondoScraper(output_dir=args.output, headless=headless)
        scraper.run_all()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
