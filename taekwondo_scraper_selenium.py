"""
Taekwondo Data Scraper using Selenium
Uses browser automation to access SimplyCompete platform data
This bypasses API restrictions by using an actual browser
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("ERROR: Selenium not installed. Install with: pip install selenium")
    print("You may also need to install ChromeDriver")
    exit(1)


class TaekwondoSeleniumScraper:
    """
    Scraper using Selenium for JavaScript-heavy sites
    """

    def __init__(self, output_dir="data", headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "athletes").mkdir(exist_ok=True)
        (self.output_dir / "rankings").mkdir(exist_ok=True)

        # Setup Chrome options
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
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            print(f"ERROR initializing Chrome driver: {e}")
            print("\nTry installing ChromeDriver:")
            print("  1. Download from: https://chromedriver.chromium.org/")
            print("  2. Or use: pip install webdriver-manager")
            raise

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def scrape_rankings_page(self) -> pd.DataFrame:
        """
        Scrape rankings from World Taekwondo ranking page
        This loads the embedded SimplyCompete iframe
        """
        print("\n[1] Scraping Rankings...")

        url = "https://www.worldtaekwondo.org/athletes/Ranking/contents"
        self.driver.get(url)

        # Wait for page to load
        time.sleep(5)

        # Take screenshot for debugging
        screenshot_file = self.output_dir / "rankings" / f"rankings_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_file))
        print(f"  [DEBUG] Screenshot saved: {screenshot_file}")

        # Try to find iframe with SimplyCompete content
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            print(f"  Found {len(iframes)} iframes")

            for i, iframe in enumerate(iframes):
                iframe_src = iframe.get_attribute('src')
                print(f"  iframe {i}: {iframe_src}")

                # Switch to iframe containing rankings
                if 'simplycompete' in iframe_src or 'ranking' in iframe_src.lower():
                    print(f"  Switching to rankings iframe...")
                    self.driver.switch_to.frame(iframe)

                    # Wait for content to load
                    time.sleep(5)

                    # Try to extract table data
                    rankings_data = self._extract_rankings_from_page()

                    # Switch back to main page
                    self.driver.switch_to.default_content()

                    if rankings_data:
                        df = pd.DataFrame(rankings_data)
                        output_file = self.output_dir / "rankings" / f"world_rankings_{datetime.now().strftime('%Y%m%d')}.csv"
                        df.to_csv(output_file, index=False)
                        print(f"  [OK] Saved {len(df)} rankings to {output_file}")
                        return df

        except Exception as e:
            print(f"  [ERROR] {e}")

        # If iframe approach fails, try to extract from main page
        rankings_data = self._extract_rankings_from_page()

        if rankings_data:
            df = pd.DataFrame(rankings_data)
            output_file = self.output_dir / "rankings" / f"world_rankings_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)
            print(f"  [OK] Saved {len(df)} rankings to {output_file}")
            return df
        else:
            print(f"  [WARN] No rankings found - check screenshot")
            # Save page source for analysis
            source_file = self.output_dir / "rankings" / f"rankings_page_source_{datetime.now().strftime('%Y%m%d')}.html"
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            return pd.DataFrame()

    def _extract_rankings_from_page(self) -> List[Dict]:
        """Extract ranking data from current page"""
        rankings = []

        try:
            # Look for table elements
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            for table in tables:
                try:
                    # Get headers
                    headers = []
                    header_cells = table.find_elements(By.TAG_NAME, 'th')
                    for cell in header_cells:
                        headers.append(cell.text.strip())

                    # Get rows
                    rows = table.find_elements(By.TAG_NAME, 'tr')

                    for row in rows[1:]:  # Skip header row
                        cells = row.find_elements(By.TAG_NAME, 'td')

                        if len(cells) >= 3:  # At least rank, name, points
                            ranking_data = {}

                            # Try to map to headers if available
                            for i, cell in enumerate(cells):
                                key = headers[i] if i < len(headers) else f'column_{i}'
                                ranking_data[key] = cell.text.strip()

                            ranking_data['scraped_date'] = datetime.now().isoformat()
                            rankings.append(ranking_data)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"  [ERROR extracting table data] {e}")

        return rankings

    def scrape_competitions_page(self) -> List[Dict]:
        """
        Scrape competitions list
        """
        print("\n[2] Scraping Competitions...")

        url = "https://www.worldtaekwondo.org/competitions/overview"
        self.driver.get(url)
        time.sleep(5)

        # Take screenshot
        screenshot_file = self.output_dir / "competitions" / f"competitions_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.save_screenshot(str(screenshot_file))

        competitions = []

        try:
            # Look for competition links
            links = self.driver.find_elements(By.TAG_NAME, 'a')

            for link in links:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and ('competition' in href.lower() or 'event' in href.lower()):
                    comp_data = {
                        'name': text,
                        'url': href,
                        'scraped_date': datetime.now().isoformat()
                    }
                    competitions.append(comp_data)

        except Exception as e:
            print(f"  [ERROR] {e}")

        if competitions:
            # Remove duplicates
            competitions = [dict(t) for t in {tuple(d.items()) for d in competitions}]

            output_file = self.output_dir / "competitions" / f"competitions_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(competitions, f, indent=2, ensure_ascii=False)

            csv_file = self.output_dir / "competitions" / f"competitions_{datetime.now().strftime('%Y%m%d')}.csv"
            pd.DataFrame(competitions).to_csv(csv_file, index=False)

            print(f"  [OK] Found {len(competitions)} competitions")
        else:
            print(f"  [WARN] No competitions found")

        return competitions

    def download_ranking_excel_files(self) -> List[str]:
        """
        Check for downloadable Excel/CSV files on the rankings page
        """
        print("\n[3] Looking for downloadable ranking files...")

        url = "https://www.worldtaekwondo.org/athletes/Ranking/contents"
        self.driver.get(url)
        time.sleep(3)

        downloaded_files = []

        try:
            # Look for download links
            links = self.driver.find_elements(By.TAG_NAME, 'a')

            for link in links:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv']):
                    print(f"  Found: {text} -> {href}")
                    downloaded_files.append({
                        'name': text,
                        'url': href,
                        'file_type': href.split('.')[-1].lower()
                    })

        except Exception as e:
            print(f"  [ERROR] {e}")

        if downloaded_files:
            output_file = self.output_dir / "rankings" / f"downloadable_files_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(downloaded_files, f, indent=2, ensure_ascii=False)

            print(f"  [OK] Found {len(downloaded_files)} downloadable files")
        else:
            print(f"  [WARN] No downloadable files found")

        return downloaded_files

    def run_full_scrape(self):
        """Run comprehensive scraping"""
        print("=" * 70)
        print("TAEKWONDO SELENIUM SCRAPER")
        print("=" * 70)

        try:
            # 1. Check for downloadable files first (easiest option)
            downloadable_files = self.download_ranking_excel_files()

            # 2. Scrape rankings
            rankings_df = self.scrape_rankings_page()

            # 3. Scrape competitions
            competitions = self.scrape_competitions_page()

            print("\n" + "=" * 70)
            print("SCRAPING COMPLETE")
            print(f"Downloadable files: {len(downloadable_files)}")
            print(f"Rankings scraped: {len(rankings_df)}")
            print(f"Competitions: {len(competitions)}")
            print(f"Data saved to: {self.output_dir.absolute()}")
            print("=" * 70)

        except Exception as e:
            print(f"\n[ERROR] Scraping failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.driver.quit()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Taekwondo Selenium Scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser window)')
    parser.add_argument('--output', default='data', help='Output directory')

    args = parser.parse_args()

    try:
        scraper = TaekwondoSeleniumScraper(
            output_dir=args.output,
            headless=args.headless
        )
        scraper.run_full_scrape()

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
