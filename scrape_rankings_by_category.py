"""
Weight Category-Aware Rankings Scraper
========================================

Scrapes World Taekwondo rankings by navigating directly to each weight category.

Strategy:
1. For each weight category, navigate to the WT rankings page
2. Wait for iframe to load
3. Extract data from the single table shown
4. Label with weight_category
5. Combine all categories into a single file

The key insight: The iframe defaults to whatever category is displayed.
We need to let the page fully load and capture what's shown, then
navigate to the category-specific URL.

Usage:
    python scrape_rankings_by_category.py [--visible] [--categories M-58kg,F-67kg]
"""

import sys
import io

# UTF-8 encoding for Windows
try:
    if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (ValueError, AttributeError):
    pass

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
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium not installed!")
    print("Run: pip install selenium")
    sys.exit(1)


# Weight categories with their SimplyCompete codes
WEIGHT_CATEGORIES = {
    'M-54kg': 'M_54',
    'M-58kg': 'M_58',
    'M-63kg': 'M_63',
    'M-68kg': 'M_68',
    'M-74kg': 'M_74',
    'M-80kg': 'M_80',
    'M-87kg': 'M_87',
    'M+87kg': 'M_O87',
    'F-46kg': 'F_46',
    'F-49kg': 'F_49',
    'F-53kg': 'F_53',
    'F-57kg': 'F_57',
    'F-62kg': 'F_62',
    'F-67kg': 'F_67',
    'F-73kg': 'F_73',
    'F+73kg': 'F_O73',
}

# SimplyCompete direct URL template - this is what gets embedded
SIMPLYCOMPETE_URL = "https://worldtkd.simplycompete.com/playerRankingV2?weightDivision={code}&year=2025&month=1"

# World Taekwondo rankings page (embeds SimplyCompete)
WT_RANKINGS_URL = "https://www.worldtaekwondo.org/athletes/Ranking/contents"


class WeightCategoryRankingsScraper:
    """
    Selenium-based scraper that captures weight_category with each athlete
    """

    def __init__(self, output_dir: str = "data", headless: bool = True):
        self.output_dir = Path(output_dir)
        self.rankings_dir = self.output_dir / 'rankings'
        self.athletes_dir = self.output_dir / 'athletes'
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
        self.athletes_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.driver = None
        self.wait = None

        # Results storage
        self.all_rankings: List[Dict] = []
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'categories_scraped': 0,
            'categories_failed': 0,
            'total_athletes': 0,
            'saudi_athletes': 0,
            'asian_athletes': 0,
            'errors': [],
            'category_results': {}
        }

        # Asian countries for filtering
        self.asian_countries = [
            'KOR', 'CHN', 'IRI', 'JPN', 'JOR', 'UZB', 'THA', 'KAZ', 'TPE', 'VIE',
            'KSA', 'UAE', 'KUW', 'QAT', 'BRN', 'OMA', 'IND', 'PAK', 'MAS', 'SIN',
            'IDN', 'PHI', 'MGL', 'PRK', 'HKG', 'MAC', 'MYA', 'LAO', 'CAM', 'BRU',
            'TJK', 'KGZ', 'TKM', 'AFG', 'NPL', 'BAN', 'SRI', 'MDV',
            'Korea', 'Republic of Korea', 'China', 'Iran', 'Islamic Republic Of Iran',
            'Japan', 'Jordan', 'Uzbekistan', 'Thailand', 'Kazakhstan', 'Chinese Taipei',
            'Vietnam', 'Saudi Arabia', 'United Arab Emirates', 'Kuwait', 'Qatar',
            'Bahrain', 'Oman', 'India', 'Pakistan', 'Malaysia', 'Singapore',
            'Indonesia', 'Philippines', 'Mongolia'
        ]

    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        print("\n[SETUP] Initializing Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            self.wait = WebDriverWait(self.driver, 30)
            print("[OK] WebDriver initialized")
            return True
        except Exception as e:
            print(f"[ERROR] WebDriver setup failed: {e}")
            self.stats['errors'].append(f"WebDriver: {str(e)}")
            return False

    def close_driver(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            print("[OK] Browser closed")

    def scrape_category_via_wt(self, weight_key: str, division_code: str) -> List[Dict]:
        """
        Scrape a single weight category via the World Taekwondo page
        This approach loads WT page, finds the iframe, and extracts data
        """
        print(f"\n[SCRAPE] {weight_key} via World Taekwondo...")
        athletes = []

        try:
            # Navigate to WT rankings page
            self.driver.get(WT_RANKINGS_URL)
            time.sleep(3)

            # Find the iframe
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            target_iframe = None

            for iframe in iframes:
                src = iframe.get_attribute('src') or ""
                if 'simplycompete' in src.lower():
                    target_iframe = iframe
                    # Modify iframe src to load specific category
                    new_src = SIMPLYCOMPETE_URL.format(code=division_code)
                    self.driver.execute_script(f"arguments[0].src = '{new_src}';", iframe)
                    print(f"[OK] Set iframe src to {weight_key}")
                    time.sleep(5)  # Wait for iframe to reload
                    break

            if not target_iframe:
                print("[WARN] No SimplyCompete iframe found")
                return athletes

            # Switch to iframe and extract
            self.driver.switch_to.frame(target_iframe)
            time.sleep(2)

            athletes = self._extract_table_data(weight_key)

            # Switch back
            self.driver.switch_to.default_content()

            return athletes

        except Exception as e:
            print(f"[ERROR] WT scrape failed: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return athletes

    def scrape_category_direct(self, weight_key: str, division_code: str) -> List[Dict]:
        """
        Try scraping directly from SimplyCompete (may be blocked by CloudFlare)
        """
        print(f"\n[SCRAPE] {weight_key} direct...")
        athletes = []

        try:
            url = SIMPLYCOMPETE_URL.format(code=division_code)
            self.driver.get(url)
            time.sleep(5)

            # Check for CloudFlare block
            page_source = self.driver.page_source.lower()
            if 'cloudflare' in page_source and 'blocked' in page_source:
                print("[BLOCKED] CloudFlare protection - trying WT method")
                return self.scrape_category_via_wt(weight_key, division_code)

            athletes = self._extract_table_data(weight_key)
            return athletes

        except Exception as e:
            print(f"[ERROR] Direct scrape failed: {e}")
            return athletes

    def _extract_table_data(self, weight_key: str) -> List[Dict]:
        """Extract data from the rankings table"""
        athletes = []

        try:
            # Wait for table
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            if not tables:
                print("[WARN] No tables found")
                return athletes

            print(f"[OK] Found {len(tables)} table(s)")

            # Get the main rankings table (usually the one with most rows)
            best_table = None
            max_rows = 0

            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    if len(rows) > max_rows:
                        max_rows = len(rows)
                        best_table = table
                except:
                    continue

            if not best_table or max_rows < 2:
                print("[WARN] No suitable table found")
                return athletes

            # Extract data using pandas read_html
            try:
                from io import StringIO
                html = best_table.get_attribute('outerHTML')
                dfs = pd.read_html(StringIO(html))

                if dfs and len(dfs[0]) > 0:
                    df = dfs[0]
                    print(f"[OK] Parsed {len(df)} rows via pandas")

                    # Map columns
                    col_map = {}
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if 'rank' in col_lower and 'rank' not in col_map:
                            col_map['rank'] = col
                        elif 'name' in col_lower:
                            col_map['athlete_name'] = col
                        elif 'nation' in col_lower or 'country' in col_lower:
                            col_map['country'] = col
                        elif 'point' in col_lower:
                            col_map['points'] = col
                        elif '↑↓' in str(col) or 'change' in col_lower:
                            col_map['rank_change'] = col

                    # Extract athletes
                    for _, row in df.iterrows():
                        athlete = {
                            'rank': row.get(col_map.get('rank', 'RANK'), ''),
                            'rank_change': row.get(col_map.get('rank_change', '↑↓'), '-'),
                            'athlete_name': row.get(col_map.get('athlete_name', 'NAME'), ''),
                            'country': row.get(col_map.get('country', 'MEMBER NATION'), ''),
                            'points': row.get(col_map.get('points', 'POINTS'), ''),
                            'gender': weight_key[0],  # M or F
                            'weight_category': weight_key,
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Validate - must have rank and name
                        if athlete['rank'] and athlete['athlete_name']:
                            rank_str = str(athlete['rank'])
                            if rank_str.isdigit():
                                athletes.append(athlete)

                                # Check for Saudi athlete
                                country_str = str(athlete['country']).upper()
                                if 'KSA' in country_str or 'SAUDI' in country_str:
                                    print(f"    [KSA] {athlete['athlete_name']} - #{athlete['rank']}")
                                    self.stats['saudi_athletes'] += 1

                                # Check for Asian athlete
                                if any(ac.upper() in country_str for ac in self.asian_countries):
                                    self.stats['asian_athletes'] += 1

            except Exception as e:
                print(f"[ERROR] Pandas extraction failed: {e}")

            # Fallback: manual extraction
            if not athletes:
                print("[FALLBACK] Trying manual extraction...")
                rows = best_table.find_elements(By.TAG_NAME, 'tr')

                for row in rows[1:]:  # Skip header
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 4:
                            athlete = {
                                'rank': cells[0].text.strip(),
                                'rank_change': cells[1].text.strip() if len(cells) > 1 else '-',
                                'athlete_name': cells[2].text.strip() if len(cells) > 2 else '',
                                'country': cells[3].text.strip() if len(cells) > 3 else '',
                                'points': cells[4].text.strip() if len(cells) > 4 else '',
                                'gender': weight_key[0],
                                'weight_category': weight_key,
                                'scraped_at': datetime.now().isoformat()
                            }

                            if athlete['rank'].isdigit() and athlete['athlete_name']:
                                athletes.append(athlete)
                    except:
                        continue

            print(f"[OK] Extracted {len(athletes)} athletes from {weight_key}")
            return athletes

        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            return athletes

    def scrape_all_categories(self, specific_categories: List[str] = None) -> pd.DataFrame:
        """Scrape all 16 weight categories"""
        print("\n" + "="*70)
        print("SCRAPING WORLD TAEKWONDO RANKINGS BY WEIGHT CATEGORY")
        print("="*70)

        if not self.setup_driver():
            return pd.DataFrame()

        try:
            # Determine categories to scrape
            if specific_categories:
                categories_to_scrape = {k: v for k, v in WEIGHT_CATEGORIES.items()
                                       if k in specific_categories}
            else:
                categories_to_scrape = WEIGHT_CATEGORIES

            print(f"\nCategories to scrape: {len(categories_to_scrape)}")

            # Scrape each category
            for weight_key, division_code in categories_to_scrape.items():
                print(f"\n{'='*50}")
                print(f"CATEGORY: {weight_key}")
                print(f"{'='*50}")

                # Try WT method first (more reliable)
                athletes = self.scrape_category_via_wt(weight_key, division_code)

                # If that fails, try direct (may hit CloudFlare)
                if not athletes:
                    print("[RETRY] Trying direct method...")
                    athletes = self.scrape_category_direct(weight_key, division_code)

                if athletes:
                    self.all_rankings.extend(athletes)
                    self.stats['categories_scraped'] += 1
                    self.stats['total_athletes'] += len(athletes)
                    self.stats['category_results'][weight_key] = {
                        'status': 'success',
                        'count': len(athletes)
                    }
                else:
                    self.stats['categories_failed'] += 1
                    self.stats['category_results'][weight_key] = {
                        'status': 'no_data',
                        'count': 0
                    }

                # Small delay between categories
                time.sleep(2)

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

        # Save combined rankings with weight_category
        combined_path = self.rankings_dir / f'world_rankings_all_{timestamp}.csv'
        df.to_csv(combined_path, index=False, encoding='utf-8-sig')
        print(f"\n[SAVED] Combined rankings: {combined_path}")

        # Save as latest
        latest_path = self.rankings_dir / 'world_rankings_latest.csv'
        df.to_csv(latest_path, index=False, encoding='utf-8-sig')
        print(f"[SAVED] Latest: {latest_path}")

        # Save by category
        if 'weight_category' in df.columns:
            for cat in df['weight_category'].unique():
                cat_df = df[df['weight_category'] == cat]
                cat_path = self.rankings_dir / f'{cat}_rankings_{timestamp}.csv'
                cat_df.to_csv(cat_path, index=False, encoding='utf-8-sig')
                print(f"[SAVED] {cat}: {len(cat_df)} athletes")

        # Save athletes file (dashboard format)
        athletes_cols = ['rank', 'athlete_name', 'country', 'points', 'weight_category', 'gender']
        available_cols = [c for c in athletes_cols if c in df.columns]
        athletes_df = df[available_cols].copy()

        if 'athlete_name' in athletes_df.columns:
            athletes_df = athletes_df.rename(columns={'athlete_name': 'name'})

        athletes_df['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        athletes_path = self.athletes_dir / 'athletes_from_rankings.csv'
        athletes_df.to_csv(athletes_path, index=False, encoding='utf-8-sig')
        print(f"[SAVED] Athletes: {athletes_path}")

        # Save Saudi athletes separately
        country_col = 'country' if 'country' in df.columns else 'MEMBER NATION'
        if country_col in df.columns:
            saudi_df = df[
                df[country_col].str.upper().str.contains('KSA|SAUDI', na=False)
            ]
            if not saudi_df.empty:
                saudi_path = self.athletes_dir / 'saudi_athletes.csv'
                saudi_df.to_csv(saudi_path, index=False, encoding='utf-8-sig')
                print(f"[SAVED] Saudi athletes: {len(saudi_df)} athletes")

        # Save stats
        self.stats['end_time'] = datetime.now().isoformat()
        stats_path = self.rankings_dir / f'scraping_stats_{timestamp}.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"[SAVED] Stats: {stats_path}")

    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*70)
        print("SCRAPING COMPLETE - SUMMARY")
        print("="*70)
        print(f"Categories scraped: {self.stats['categories_scraped']}/16")
        print(f"Categories failed: {self.stats['categories_failed']}")
        print(f"Total athletes: {self.stats['total_athletes']}")
        print(f"Saudi athletes: {self.stats['saudi_athletes']}")
        print(f"Asian athletes: {self.stats['asian_athletes']}")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:5]:
                print(f"  - {err}")

        print("\n" + "-"*70)
        print("Category Results:")
        for cat, result in self.stats['category_results'].items():
            status = result.get('status', 'unknown')
            count = result.get('count', 0)
            icon = '✓' if status == 'success' else '✗'
            print(f"  {icon} {cat}: {status} ({count} athletes)")

        print("="*70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrape World Taekwondo Rankings by Weight Category')
    parser.add_argument('--output', '-o', default='data', help='Output directory')
    parser.add_argument('--visible', '-v', action='store_true', help='Show browser')
    parser.add_argument('--categories', '-c', type=str, help='Specific categories (e.g., M-58kg,F-67kg)')

    args = parser.parse_args()

    # Parse specific categories if provided
    specific_cats = None
    if args.categories:
        specific_cats = [c.strip() for c in args.categories.split(',')]

    scraper = WeightCategoryRankingsScraper(
        output_dir=args.output,
        headless=not args.visible
    )

    print("\n" + "="*70)
    print("WORLD TAEKWONDO RANKINGS SCRAPER (By Weight Category)")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output: {args.output}")
    print(f"Headless: {not args.visible}")
    if specific_cats:
        print(f"Categories: {specific_cats}")
    print("="*70)

    # Run scraper
    df = scraper.scrape_all_categories(specific_categories=specific_cats)

    # Save results
    scraper.save_results(df)

    # Print summary
    scraper.print_summary()

    return scraper.stats['categories_scraped'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
