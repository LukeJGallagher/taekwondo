"""
Scrape World Taekwondo Rankings for ALL 16 Weight Categories
============================================================

This scraper fetches rankings for each weight category separately,
ensuring we capture the weight_category field with each athlete record.

The World Taekwondo rankings page uses a SimplyCompete iframe with
dropdown selectors for:
- Gender (Male/Female)
- Weight Category (-54kg, -58kg, etc.)

This script iterates through all combinations to get complete rankings.
"""

import sys
import io

# UTF-8 encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass

import os
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException,
        StaleElementReferenceException, ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium not installed! Run: pip install selenium")
    sys.exit(1)


# All weight categories
WEIGHT_CATEGORIES = {
    'M': {
        'name': 'Male',
        'categories': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg']
    },
    'F': {
        'name': 'Female',
        'categories': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
    }
}


class WeightCategoryRankingsScraper:
    """
    Scrape World Taekwondo Rankings by Weight Category
    """

    RANKINGS_URL = 'https://www.worldtaekwondo.org/athletes/Ranking/contents'

    def __init__(self, output_dir: str = "data", headless: bool = True, visible: bool = False):
        self.output_dir = Path(output_dir)
        self.rankings_dir = self.output_dir / 'rankings'
        self.rankings_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless and not visible
        self.driver = None
        self.wait = None

        # Results
        self.all_rankings = []
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'categories_scraped': 0,
            'total_athletes': 0,
            'saudi_athletes': 0,
            'asian_athletes': 0,
            'errors': [],
            'categories_status': {}
        }

    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        print("\n[SETUP] Initializing Chrome WebDriver...")

        options = Options()
        if self.headless:
            options.add_argument('--headless=new')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Suppress logging
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            print("[OK] Chrome WebDriver initialized")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            return False

    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                print("[OK] WebDriver closed")
            except:
                pass

    def navigate_to_rankings(self):
        """Navigate to rankings page and wait for iframe"""
        print(f"\n[NAV] Loading rankings page: {self.RANKINGS_URL}")

        try:
            self.driver.get(self.RANKINGS_URL)
            time.sleep(3)  # Wait for page load

            # Find and switch to SimplyCompete iframe
            print("[IFRAME] Looking for SimplyCompete iframe...")

            # Try multiple iframe selectors
            iframe_selectors = [
                "iframe[src*='simplycompete']",
                "iframe[src*='ranking']",
                "iframe.ranking-iframe",
                "iframe"
            ]

            iframe = None
            for selector in iframe_selectors:
                try:
                    iframe = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if iframe:
                        print(f"[OK] Found iframe with selector: {selector}")
                        break
                except:
                    continue

            if not iframe:
                print("[ERROR] Could not find rankings iframe")
                return False

            # Switch to iframe
            self.driver.switch_to.frame(iframe)
            time.sleep(2)
            print("[OK] Switched to rankings iframe")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to navigate: {e}")
            return False

    def select_weight_category(self, gender: str, category: str) -> bool:
        """
        Select a specific weight category using dropdown

        Args:
            gender: 'M' or 'F'
            category: e.g., '-58kg', '-67kg'

        Returns:
            True if selection successful
        """
        gender_name = WEIGHT_CATEGORIES[gender]['name']
        print(f"\n[SELECT] Selecting {gender_name} {category}...")

        try:
            # Find gender selector - try multiple approaches
            gender_selectors = [
                "select[name*='gender']",
                "select[id*='gender']",
                "select.gender-select",
                "#genderSelect",
                "select:first-of-type"
            ]

            gender_select = None
            for selector in gender_selectors:
                try:
                    gender_select = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if gender_select:
                        break
                except:
                    continue

            # Find weight category selector
            weight_selectors = [
                "select[name*='weight']",
                "select[name*='category']",
                "select[id*='weight']",
                "select.weight-select",
                "#weightSelect",
                "select:nth-of-type(2)"
            ]

            weight_select = None
            for selector in weight_selectors:
                try:
                    weight_select = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if weight_select:
                        break
                except:
                    continue

            # Try to select values
            if gender_select:
                try:
                    select = Select(gender_select)
                    # Try different value formats
                    for value in [gender, gender_name, gender_name.upper(), gender.lower()]:
                        try:
                            select.select_by_value(value)
                            break
                        except:
                            try:
                                select.select_by_visible_text(value)
                                break
                            except:
                                continue
                    time.sleep(1)
                except Exception as e:
                    print(f"[WARN] Could not select gender: {e}")

            if weight_select:
                try:
                    select = Select(weight_select)
                    # Try different value formats
                    for value in [category, category.replace('kg', ''), category.replace('-', '').replace('+', 'over')]:
                        try:
                            select.select_by_value(value)
                            break
                        except:
                            try:
                                select.select_by_visible_text(value)
                                break
                            except:
                                continue
                    time.sleep(2)  # Wait for data to load
                except Exception as e:
                    print(f"[WARN] Could not select weight category: {e}")

            # Try clicking a search/filter button if available
            search_buttons = [
                "button[type='submit']",
                "button.search-btn",
                "input[type='submit']",
                ".filter-btn"
            ]

            for selector in search_buttons:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    btn.click()
                    time.sleep(2)
                    break
                except:
                    continue

            return True

        except Exception as e:
            print(f"[ERROR] Failed to select category: {e}")
            return False

    def extract_rankings_table(self, gender: str, category: str) -> List[Dict]:
        """Extract rankings data from current table"""
        print(f"[EXTRACT] Extracting data for {WEIGHT_CATEGORIES[gender]['name']} {category}...")

        athletes = []

        try:
            # Wait for table to load
            time.sleep(2)

            # Find table - try multiple selectors
            table_selectors = [
                "table.ranking-table",
                "table.data-table",
                "table[id*='ranking']",
                "table.table",
                "table"
            ]

            table = None
            for selector in table_selectors:
                try:
                    tables = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for t in tables:
                        if t.text.strip():
                            table = t
                            break
                except:
                    continue
                if table:
                    break

            if not table:
                print("[WARN] No table found")
                return athletes

            # Extract rows
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"[OK] Found {len(rows)} rows")

            # Process each row (skip header)
            for row in rows[1:]:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        athlete = {
                            'rank': cells[0].text.strip() if len(cells) > 0 else '',
                            'rank_change': cells[1].text.strip() if len(cells) > 1 else '',
                            'athlete_name': cells[2].text.strip() if len(cells) > 2 else '',
                            'country': cells[3].text.strip() if len(cells) > 3 else '',
                            'points': cells[4].text.strip() if len(cells) > 4 else '',
                            'gender': gender,
                            'weight_category': f"{WEIGHT_CATEGORIES[gender]['name'][0]}{category}",  # e.g., "M-58kg"
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Clean up data
                        if athlete['rank'] and athlete['athlete_name']:
                            athletes.append(athlete)

                except Exception as e:
                    continue

            print(f"[OK] Extracted {len(athletes)} athletes")
            return athletes

        except Exception as e:
            print(f"[ERROR] Failed to extract table: {e}")
            return athletes

    def scrape_single_category_direct(self, gender: str, category: str) -> List[Dict]:
        """
        Direct URL approach - construct URL for specific category
        Some ranking systems use URL parameters for filtering
        """
        # Try direct URL approach
        category_urls = [
            f"https://www.worldtaekwondo.org/athletes/Ranking/contents?gender={gender}&weight={category}",
            f"https://worldtaekwondo.simplycompete.com/rankings?gender={gender}&weight={category}",
        ]

        # This is a fallback method - main approach uses dropdowns
        return []

    def scrape_all_categories(self) -> pd.DataFrame:
        """Scrape rankings for all 16 weight categories"""
        print("\n" + "="*70)
        print("SCRAPING ALL WEIGHT CATEGORIES")
        print("="*70)

        if not self.setup_driver():
            return pd.DataFrame()

        try:
            if not self.navigate_to_rankings():
                print("[ERROR] Could not navigate to rankings page")
                return pd.DataFrame()

            # Scrape each gender and weight category
            for gender in ['M', 'F']:
                gender_info = WEIGHT_CATEGORIES[gender]
                print(f"\n{'='*50}")
                print(f"GENDER: {gender_info['name']}")
                print(f"{'='*50}")

                for category in gender_info['categories']:
                    category_key = f"{gender}{category}"
                    print(f"\n--- Processing {category_key} ---")

                    try:
                        # Select the weight category
                        self.select_weight_category(gender, category)

                        # Extract rankings
                        athletes = self.extract_rankings_table(gender, category)

                        if athletes:
                            self.all_rankings.extend(athletes)
                            self.stats['categories_scraped'] += 1
                            self.stats['total_athletes'] += len(athletes)
                            self.stats['categories_status'][category_key] = {
                                'status': 'success',
                                'count': len(athletes)
                            }

                            # Check for Saudi athletes
                            saudi = [a for a in athletes if 'KSA' in a.get('country', '').upper() or 'SAUDI' in a.get('country', '').upper()]
                            if saudi:
                                self.stats['saudi_athletes'] += len(saudi)
                                print(f"[KSA] Found {len(saudi)} Saudi athlete(s)!")
                                for s in saudi:
                                    print(f"      - {s['athlete_name']} (Rank #{s['rank']})")
                        else:
                            self.stats['categories_status'][category_key] = {
                                'status': 'empty',
                                'count': 0
                            }
                            print(f"[WARN] No data extracted for {category_key}")

                        time.sleep(1)  # Rate limiting

                    except Exception as e:
                        self.stats['errors'].append(f"{category_key}: {str(e)}")
                        self.stats['categories_status'][category_key] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        print(f"[ERROR] Failed to scrape {category_key}: {e}")

            # Create DataFrame
            if self.all_rankings:
                df = pd.DataFrame(self.all_rankings)
                return df
            else:
                print("[WARN] No rankings data collected")
                return pd.DataFrame()

        finally:
            self.close_driver()

    def save_results(self, df: pd.DataFrame):
        """Save scraped data to files"""
        if df.empty:
            print("[WARN] No data to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d')

        # Save combined file
        combined_path = self.rankings_dir / f'world_rankings_all_categories_{timestamp}.csv'
        df.to_csv(combined_path, index=False)
        print(f"\n[SAVED] Combined rankings: {combined_path}")

        # Also save as world_rankings_latest.csv
        latest_path = self.rankings_dir / 'world_rankings_latest.csv'
        df.to_csv(latest_path, index=False)
        print(f"[SAVED] Latest rankings: {latest_path}")

        # Save by gender
        for gender in ['M', 'F']:
            gender_df = df[df['gender'] == gender]
            if not gender_df.empty:
                gender_name = 'male' if gender == 'M' else 'female'
                gender_path = self.rankings_dir / f'world_rankings_{gender_name}_{timestamp}.csv'
                gender_df.to_csv(gender_path, index=False)
                print(f"[SAVED] {gender_name.title()} rankings: {gender_path}")

        # Update athletes file
        athletes_dir = self.output_dir / 'athletes'
        athletes_dir.mkdir(exist_ok=True)

        athletes_df = df[['rank', 'athlete_name', 'country', 'points', 'weight_category', 'gender']].copy()
        athletes_df = athletes_df.rename(columns={'athlete_name': 'name'})
        athletes_df['last_updated'] = datetime.now().strftime('%Y-%m-%d')

        athletes_path = athletes_dir / 'athletes_from_rankings.csv'
        athletes_df.to_csv(athletes_path, index=False)
        print(f"[SAVED] Athletes: {athletes_path}")

        # Save Saudi-specific file
        saudi_df = df[
            df['country'].str.upper().str.contains('KSA|SAUDI', na=False)
        ]
        if not saudi_df.empty:
            saudi_path = athletes_dir / 'saudi_athletes.csv'
            saudi_df.to_csv(saudi_path, index=False)
            print(f"[SAVED] Saudi athletes: {saudi_path} ({len(saudi_df)} athletes)")

        # Save stats
        self.stats['end_time'] = datetime.now().isoformat()
        stats_path = self.rankings_dir / f'scraping_stats_{timestamp}.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"[SAVED] Stats: {stats_path}")

    def run(self) -> bool:
        """Main entry point"""
        print("\n" + "="*70)
        print("WORLD TAEKWONDO RANKINGS SCRAPER - ALL WEIGHT CATEGORIES")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_dir}")
        print(f"Headless mode: {self.headless}")
        print("="*70)

        # Scrape all categories
        df = self.scrape_all_categories()

        # Save results
        self.save_results(df)

        # Print summary
        print("\n" + "="*70)
        print("SCRAPING COMPLETE - SUMMARY")
        print("="*70)
        print(f"Categories scraped: {self.stats['categories_scraped']}/16")
        print(f"Total athletes: {self.stats['total_athletes']}")
        print(f"Saudi athletes found: {self.stats['saudi_athletes']}")
        print(f"Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\nErrors encountered:")
            for err in self.stats['errors'][:5]:
                print(f"  - {err}")

        print("="*70)

        return self.stats['categories_scraped'] > 0


def main():
    parser = argparse.ArgumentParser(description='Scrape World Taekwondo Rankings by Weight Category')
    parser.add_argument('--output', '-o', default='data', help='Output directory')
    parser.add_argument('--visible', '-v', action='store_true', help='Show browser (non-headless)')

    args = parser.parse_args()

    scraper = WeightCategoryRankingsScraper(
        output_dir=args.output,
        headless=not args.visible,
        visible=args.visible
    )

    success = scraper.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
