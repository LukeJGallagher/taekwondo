"""
Scrape Olympic Games Results from World Taekwondo
Handles dynamic JavaScript-loaded content
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from datetime import datetime

class OlympicScraper:
    def __init__(self, output_dir="data_all_categories/olympics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.olympics_url = "https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents"

        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')

        self.downloadable_files = []
        self.olympics_data = []

    def scrape_olympics(self):
        """Scrape Olympic Games results page"""
        print(f"\n{'='*70}")
        print("SCRAPING OLYMPIC GAMES RESULTS")
        print(f"{'='*70}")
        print(f"\nURL: {self.olympics_url}")

        driver = webdriver.Chrome(options=self.options)

        try:
            driver.get(self.olympics_url)
            print("  Waiting for page to load...")

            # Wait for content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Give extra time for JavaScript to render
            time.sleep(5)

            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Save full HTML for analysis
            html_file = self.output_dir / "olympics_page.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"  Saved HTML: {html_file.name}")

            # Look for competition links/sections
            print("\n  Looking for Olympic competitions...")

            # Try various selectors that might contain Olympics data
            selectors = [
                ('a[href*="olympic"]', 'Olympic links'),
                ('.competition-item', 'Competition items'),
                ('.news-item', 'News items'),
                ('.event-item', 'Event items'),
                ('tbody tr', 'Table rows'),
                ('.list-item', 'List items')
            ]

            for selector, description in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\n  Found {len(elements)} {description}")

                    for elem in elements[:10]:  # Limit to first 10
                        try:
                            text = elem.text.strip()
                            if text and len(text) > 5:
                                print(f"    - {text[:100]}")

                                # Check for downloadable files
                                links = elem.find_elements(By.TAG_NAME, 'a')
                                for link in links:
                                    href = link.get_attribute('href')
                                    if href and (href.endswith('.pdf') or href.endswith('.xlsx') or href.endswith('.xls')):
                                        self.downloadable_files.append({
                                            'url': href,
                                            'text': link.text.strip()
                                        })
                                        print(f"      [DOWNLOAD] {href}")

                        except Exception as e:
                            continue

            # Look specifically for Paris 2024, Tokyo 2020, Rio 2016, etc.
            print("\n  Searching for specific Olympics...")
            olympics_keywords = [
                'Paris 2024', 'Tokyo 2020', 'Rio 2016', 'London 2012',
                'Beijing 2008', 'Athens 2004', 'Sydney 2000'
            ]

            for keyword in olympics_keywords:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                if elements:
                    print(f"\n  Found {keyword}:")
                    for elem in elements[:5]:
                        try:
                            # Get parent element for context
                            parent = elem.find_element(By.XPATH, "./..")
                            print(f"    - {parent.text.strip()[:150]}")
                        except:
                            print(f"    - {elem.text.strip()[:150]}")

            # Look for tables with results
            print("\n  Looking for result tables...")
            tables = driver.find_elements(By.TAG_NAME, 'table')
            if tables:
                print(f"  Found {len(tables)} tables")

                for idx, table in enumerate(tables):
                    try:
                        # Get table HTML
                        table_html = table.get_attribute('outerHTML')
                        table_soup = BeautifulSoup(table_html, 'html.parser')

                        # Extract table data
                        rows = table_soup.find_all('tr')
                        if len(rows) > 1:
                            print(f"\n    Table {idx+1}: {len(rows)} rows")

                            # Save table
                            table_file = self.output_dir / f"olympics_table_{idx+1}.html"
                            with open(table_file, 'w', encoding='utf-8') as f:
                                f.write(table_html)
                            print(f"    Saved: {table_file.name}")

                            # Try to convert to structured data
                            table_data = []
                            headers = [th.text.strip() for th in rows[0].find_all(['th', 'td'])]

                            for row in rows[1:11]:  # First 10 data rows
                                cells = [td.text.strip() for td in row.find_all('td')]
                                if cells:
                                    table_data.append(dict(zip(headers, cells)))

                            if table_data:
                                self.olympics_data.extend(table_data)
                                print(f"    Sample: {table_data[0]}")

                    except Exception as e:
                        print(f"    Error processing table: {e}")

            # Look for PDF/Excel download buttons
            print("\n  Looking for downloadable files...")
            download_buttons = driver.find_elements(By.XPATH,
                "//*[contains(text(), 'PDF') or contains(text(), 'Download') or contains(text(), 'EXCEL')]")

            for button in download_buttons:
                try:
                    parent = button.find_element(By.XPATH, "./..")
                    link = parent.get_attribute('href')
                    if link:
                        self.downloadable_files.append({
                            'url': link,
                            'text': button.text.strip()
                        })
                        print(f"    [DOWNLOAD] {link}")
                except:
                    continue

        except TimeoutException:
            print("  [ERROR] Page load timeout")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()

    def save_results(self):
        """Save all scraped data"""
        print(f"\n{'='*70}")
        print("SAVING RESULTS")
        print(f"{'='*70}")

        # Save downloadable files list
        if self.downloadable_files:
            files_json = self.output_dir / "downloadable_files.json"
            with open(files_json, 'w', encoding='utf-8') as f:
                json.dump(self.downloadable_files, f, indent=2)
            print(f"\n[SAVED] {len(self.downloadable_files)} downloadable files")
            print(f"  File: {files_json}")

            for file_info in self.downloadable_files:
                print(f"    - {file_info['url']}")
        else:
            print("\n[INFO] No downloadable files found")

        # Save extracted Olympics data
        if self.olympics_data:
            data_json = self.output_dir / "olympics_data.json"
            with open(data_json, 'w', encoding='utf-8') as f:
                json.dump(self.olympics_data, f, indent=2)
            print(f"\n[SAVED] {len(self.olympics_data)} data records")
            print(f"  File: {data_json}")
        else:
            print("\n[INFO] No structured data extracted")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'url': self.olympics_url,
            'downloadable_files_count': len(self.downloadable_files),
            'data_records_count': len(self.olympics_data),
            'output_directory': str(self.output_dir)
        }

        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"\n[SUMMARY] {summary_file}")
        print(f"{'='*70}")

def main():
    scraper = OlympicScraper()

    try:
        scraper.scrape_olympics()
        scraper.save_results()

        print("\n[COMPLETE] Olympic Games scraping finished")
        print(f"Check: {scraper.output_dir}")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
