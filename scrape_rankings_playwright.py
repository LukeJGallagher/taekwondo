"""
Playwright-based World Taekwondo Rankings Scraper
==================================================

Scrapes all 16 weight categories from the SimplyCompete rankings system,
capturing weight_category with each athlete record.

Features:
- Async/await for efficient operations
- Auto-retry with exponential backoff
- Handles iframe navigation
- Saudi athlete highlighting
- Saves to dashboard-compatible format

Usage:
    pip install playwright
    playwright install chromium
    python scrape_rankings_playwright.py [--visible] [--categories M-58kg,F-67kg]
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import sys

try:
    from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Weight categories configuration
WEIGHT_CATEGORIES = {
    'M': {
        'name': 'Male',
        'code': 'M',
        'categories': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg']
    },
    'F': {
        'name': 'Female',
        'code': 'F',
        'categories': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
    }
}

# SimplyCompete weight division codes (discovered from page)
WEIGHT_DIVISION_CODES = {
    'M-54kg': 'M_54', 'M-58kg': 'M_58', 'M-63kg': 'M_63', 'M-68kg': 'M_68',
    'M-74kg': 'M_74', 'M-80kg': 'M_80', 'M-87kg': 'M_87', 'M+87kg': 'M_O87',
    'F-46kg': 'F_46', 'F-49kg': 'F_49', 'F-53kg': 'F_53', 'F-57kg': 'F_57',
    'F-62kg': 'F_62', 'F-67kg': 'F_67', 'F-73kg': 'F_73', 'F+73kg': 'F_O73',
}


class PlaywrightRankingsScraper:
    """
    Async Playwright-based scraper for World Taekwondo rankings
    """

    RANKINGS_URL = 'https://worldtkd.simplycompete.com/playerRankingV2'

    def __init__(self, output_dir: str = "data", headless: bool = True):
        self.output_dir = Path(output_dir)
        self.rankings_dir = self.output_dir / 'rankings'
        self.athletes_dir = self.output_dir / 'athletes'
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
        self.athletes_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

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
            'Republic of Korea', 'Korea', 'China', 'Iran', 'Japan', 'Jordan',
            'Uzbekistan', 'Thailand', 'Kazakhstan', 'Chinese Taipei', 'Vietnam',
            'Saudi Arabia', 'United Arab Emirates', 'Kuwait', 'Qatar', 'Bahrain',
            'Oman', 'India', 'Pakistan', 'Malaysia', 'Singapore', 'Indonesia',
            'Philippines', 'Mongolia'
        ]

    async def setup(self):
        """Initialize Playwright browser"""
        print("\n[SETUP] Initializing Playwright browser...")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        # Create context with realistic viewport
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        self.page = await context.new_page()
        print("[OK] Browser initialized")

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            print("[OK] Browser closed")

    async def navigate_to_rankings(self) -> bool:
        """Navigate to rankings page"""
        print(f"\n[NAV] Loading rankings page...")

        try:
            # Use 'domcontentloaded' instead of 'networkidle' - more reliable for dynamic pages
            await self.page.goto(self.RANKINGS_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Allow dynamic content and iframes to load

            # Check if page loaded
            title = await self.page.title()
            print(f"[OK] Page loaded: {title}")
            return True

        except Exception as e:
            print(f"[ERROR] Navigation failed: {e}")
            self.stats['errors'].append(f"Navigation: {str(e)}")
            return False

    async def select_weight_category(self, gender: str, category: str) -> bool:
        """
        Select a weight category using the dropdown

        Args:
            gender: 'M' or 'F'
            category: e.g., '-58kg', '+87kg'
        """
        weight_key = f"{gender}{category}"
        division_code = WEIGHT_DIVISION_CODES.get(weight_key)

        if not division_code:
            print(f"[WARN] Unknown weight category: {weight_key}")
            return False

        print(f"[SELECT] Selecting {weight_key} (code: {division_code})...")

        try:
            # Try to find and click the weight division dropdown
            # SimplyCompete uses various UI frameworks, try multiple approaches

            # Approach 1: Direct URL parameter change
            url_with_params = f"{self.RANKINGS_URL}?weightDivision={division_code}&year=2025&month=1"
            await self.page.goto(url_with_params, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(8)  # Wait for data to load - SimplyCompete is slow

            # Debug: Take screenshot and save page source for analysis
            if not self.headless:
                screenshots_dir = self.output_dir / 'debug'
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                await self.page.screenshot(path=str(screenshots_dir / f'{weight_key}_screenshot.png'))
                html_content = await self.page.content()
                with open(screenshots_dir / f'{weight_key}_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"[DEBUG] Saved screenshot and HTML to {screenshots_dir}")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to select {weight_key}: {e}")
            return False

    async def extract_rankings_table(self, gender: str, category: str) -> List[Dict]:
        """Extract rankings data from the current page"""
        weight_key = f"{gender}{category}"
        print(f"[EXTRACT] Extracting {weight_key} rankings...")

        athletes = []

        try:
            # Check for iframes first - SimplyCompete embeds content in iframes
            frames = self.page.frames
            target_frame = self.page

            for frame in frames:
                if 'simplycompete' in frame.url or frame != self.page.main_frame:
                    try:
                        table_check = await frame.query_selector('table')
                        if table_check:
                            target_frame = frame
                            print(f"[OK] Found data in iframe: {frame.url[:50]}...")
                            break
                    except Exception:
                        continue

            # Wait for table to appear (with longer timeout)
            await target_frame.wait_for_selector('table', timeout=15000)

            # Get all table rows
            rows = await target_frame.query_selector_all('table tbody tr')

            if not rows:
                # Try alternative: table without tbody
                rows = await target_frame.query_selector_all('table tr')

            print(f"[OK] Found {len(rows)} rows")

            for row in rows:
                try:
                    cells = await row.query_selector_all('td')

                    if len(cells) >= 4:
                        # Extract cell text
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())

                        # Parse athlete data
                        # Typical format: Rank, Change, Name, Country, Points
                        athlete = {
                            'rank': cell_texts[0] if len(cell_texts) > 0 else '',
                            'rank_change': cell_texts[1] if len(cell_texts) > 1 else '',
                            'athlete_name': cell_texts[2] if len(cell_texts) > 2 else '',
                            'country': cell_texts[3] if len(cell_texts) > 3 else '',
                            'points': cell_texts[4] if len(cell_texts) > 4 else '',
                            'gender': gender,
                            'weight_category': weight_key,
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Validate - must have rank and name
                        if athlete['rank'] and athlete['athlete_name'] and athlete['rank'].isdigit():
                            athletes.append(athlete)

                            # Check for Saudi athlete
                            country_upper = athlete['country'].upper()
                            if 'KSA' in country_upper or 'SAUDI' in country_upper:
                                print(f"    [KSA] Found: {athlete['athlete_name']} - Rank #{athlete['rank']}")
                                self.stats['saudi_athletes'] += 1

                            # Check for Asian athlete
                            if any(ac.upper() in country_upper for ac in self.asian_countries):
                                self.stats['asian_athletes'] += 1

                except Exception as e:
                    continue

            print(f"[OK] Extracted {len(athletes)} athletes from {weight_key}")
            return athletes

        except PlaywrightTimeout:
            print(f"[WARN] Timeout waiting for table in {weight_key}")
            return athletes
        except Exception as e:
            print(f"[ERROR] Extraction failed for {weight_key}: {e}")
            return athletes

    async def scrape_category(self, gender: str, category: str, retry_count: int = 3) -> List[Dict]:
        """Scrape a single weight category with retry logic"""
        weight_key = f"{gender}{category}"

        for attempt in range(retry_count):
            try:
                # Select the category
                if not await self.select_weight_category(gender, category):
                    continue

                # Extract data
                athletes = await self.extract_rankings_table(gender, category)

                if athletes:
                    self.stats['category_results'][weight_key] = {
                        'status': 'success',
                        'count': len(athletes),
                        'attempt': attempt + 1
                    }
                    return athletes
                else:
                    print(f"[RETRY] No data for {weight_key}, attempt {attempt + 1}/{retry_count}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                print(f"[ERROR] Attempt {attempt + 1} failed for {weight_key}: {e}")
                await asyncio.sleep(2 ** attempt)

        # All retries failed
        self.stats['category_results'][weight_key] = {
            'status': 'failed',
            'count': 0,
            'error': 'All retries exhausted'
        }
        self.stats['categories_failed'] += 1
        return []

    async def scrape_all_categories(self, specific_categories: List[str] = None) -> pd.DataFrame:
        """
        Scrape all 16 weight categories (or specific ones)

        Args:
            specific_categories: Optional list like ['M-58kg', 'F-67kg']
        """
        print("\n" + "="*70)
        print("SCRAPING WORLD TAEKWONDO RANKINGS")
        print("="*70)

        await self.setup()

        try:
            # Initial navigation
            if not await self.navigate_to_rankings():
                print("[ERROR] Could not access rankings page")
                return pd.DataFrame()

            # Determine categories to scrape
            categories_to_scrape = []

            if specific_categories:
                categories_to_scrape = specific_categories
            else:
                # All categories
                for gender in ['M', 'F']:
                    for cat in WEIGHT_CATEGORIES[gender]['categories']:
                        categories_to_scrape.append(f"{gender}{cat}")

            print(f"\nCategories to scrape: {len(categories_to_scrape)}")

            # Scrape each category
            for weight_key in categories_to_scrape:
                gender = weight_key[0]
                category = weight_key[1:]

                print(f"\n{'='*50}")
                print(f"CATEGORY: {weight_key}")
                print(f"{'='*50}")

                athletes = await self.scrape_category(gender, category)

                if athletes:
                    self.all_rankings.extend(athletes)
                    self.stats['categories_scraped'] += 1
                    self.stats['total_athletes'] += len(athletes)

                # Rate limiting
                await asyncio.sleep(1)

            # Create DataFrame
            if self.all_rankings:
                df = pd.DataFrame(self.all_rankings)
                return df
            else:
                print("[WARN] No rankings data collected")
                return pd.DataFrame()

        finally:
            await self.close()

    def save_results(self, df: pd.DataFrame):
        """Save scraped data to files"""
        if df.empty:
            print("[WARN] No data to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d')

        # Save combined rankings
        combined_path = self.rankings_dir / f'world_rankings_all_{timestamp}.csv'
        df.to_csv(combined_path, index=False)
        print(f"\n[SAVED] Combined rankings: {combined_path}")

        # Save as latest
        latest_path = self.rankings_dir / 'world_rankings_latest.csv'
        df.to_csv(latest_path, index=False)
        print(f"[SAVED] Latest: {latest_path}")

        # Save athletes file (dashboard format)
        athletes_df = df[['rank', 'athlete_name', 'country', 'points', 'weight_category', 'gender']].copy()
        athletes_df = athletes_df.rename(columns={'athlete_name': 'name'})
        athletes_df['last_updated'] = datetime.now().strftime('%Y-%m-%d')

        athletes_path = self.athletes_dir / 'athletes_from_rankings.csv'
        athletes_df.to_csv(athletes_path, index=False)
        print(f"[SAVED] Athletes: {athletes_path}")

        # Save Saudi athletes separately
        saudi_df = df[
            df['country'].str.upper().str.contains('KSA|SAUDI', na=False)
        ]
        if not saudi_df.empty:
            saudi_path = self.athletes_dir / 'saudi_athletes.csv'
            saudi_df.to_csv(saudi_path, index=False)
            print(f"[SAVED] Saudi athletes: {saudi_path} ({len(saudi_df)} athletes)")

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

        print("="*70)


async def main():
    """Main entry point"""
    if not PLAYWRIGHT_AVAILABLE:
        print("[ERROR] Playwright not installed!")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Scrape World Taekwondo Rankings')
    parser.add_argument('--output', '-o', default='data', help='Output directory')
    parser.add_argument('--visible', '-v', action='store_true', help='Show browser')
    parser.add_argument('--categories', '-c', type=str, help='Specific categories (e.g., M-58kg,F-67kg)')

    args = parser.parse_args()

    # Parse specific categories if provided
    specific_cats = None
    if args.categories:
        specific_cats = [c.strip() for c in args.categories.split(',')]

    scraper = PlaywrightRankingsScraper(
        output_dir=args.output,
        headless=not args.visible
    )

    print("\n" + "="*70)
    print("WORLD TAEKWONDO RANKINGS SCRAPER (Playwright)")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output: {args.output}")
    print(f"Headless: {not args.visible}")
    if specific_cats:
        print(f"Categories: {specific_cats}")
    print("="*70)

    # Run scraper
    df = await scraper.scrape_all_categories(specific_categories=specific_cats)

    # Save results
    scraper.save_results(df)

    # Print summary
    scraper.print_summary()

    return scraper.stats['categories_scraped'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
