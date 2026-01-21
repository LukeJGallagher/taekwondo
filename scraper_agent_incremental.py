"""
Incremental Taekwondo Web Scraping Agent
Smart update system that:
1. Only scrapes new/changed data
2. Checks back 30 days for corrections
3. Detects ranking changes
4. Tracks data freshness
5. Skips unchanged content
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import time
import json
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium not installed!")
    exit(1)


class IncrementalScraperAgent:
    """
    Smart incremental scraper that only updates changed data
    """

    COMPETITION_CATEGORIES = {
        'rankings': {
            'url': 'https://www.worldtaekwondo.org/athletes/Ranking/contents',
            'name': 'World Rankings',
            'priority': 1,
            'update_frequency': 'daily',  # Check daily
            'has_iframe': True
        },
        'olympics': {
            'url': 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents',
            'name': 'Olympic Games',
            'priority': 2,
            'update_frequency': 'monthly',  # Rarely changes
            'has_iframe': False
        },
        'world_champs_senior': {
            'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTC/list',
            'name': 'World Championships',
            'priority': 3,
            'update_frequency': 'weekly',  # New competitions added
            'has_iframe': False
        },
        # ===== ASIAN GAMES & CONTINENTAL =====
        'asian_games': {
            'url': 'https://www.worldtaekwondo.org/competitions/AsianGames/contents',
            'name': 'Asian Games',
            'priority': 4,
            'update_frequency': 'weekly',  # Critical for 2026 tracking
            'has_iframe': False,
            'strategic_importance': 'critical'  # For Asian Games 2026 focus
        },
        'asian_champs': {
            'url': 'https://www.worldtaekwondo.org/competitions/AsianChampionships/contents',
            'name': 'Asian Championships',
            'priority': 5,
            'update_frequency': 'weekly',  # Key qualifying events
            'has_iframe': False,
            'strategic_importance': 'high'
        },
        # ===== GRAND PRIX SERIES (Ranking Points) =====
        'grand_prix': {
            'url': 'https://www.worldtaekwondo.org/competitions/GrandPrix/contents',
            'name': 'Grand Prix Series',
            'priority': 6,
            'update_frequency': 'weekly',
            'has_iframe': False,
            'strategic_importance': 'high'
        },
        'grand_slam': {
            'url': 'https://www.worldtaekwondo.org/competitions/GrandSlam/contents',
            'name': 'Grand Slam',
            'priority': 7,
            'update_frequency': 'weekly',
            'has_iframe': False,
            'strategic_importance': 'high'
        },
        # ===== PRESIDENTS CUP (Regional) =====
        'presidents_cup_asia': {
            'url': 'https://www.worldtaekwondo.org/competitions/PresidentsCup/Asia/contents',
            'name': 'Presidents Cup Asia',
            'priority': 8,
            'update_frequency': 'monthly',
            'has_iframe': False,
            'strategic_importance': 'medium'
        }
    }

    def __init__(self, output_dir="data_incremental", lookback_days=30, headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.lookback_days = lookback_days  # Check back 30 days for corrections
        self.headless = headless
        self.driver = None
        self.wait = None

        # Metadata tracking
        self.metadata_file = self.output_dir / ".scrape_history.json"
        self.metadata = self.load_metadata()

        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'mode': 'incremental',
            'categories_checked': 0,
            'categories_updated': 0,
            'categories_skipped': 0,
            'new_data_rows': 0,
            'changed_data_rows': 0,
            'unchanged_categories': [],
            'changes_detected': []
        }

        # Create category folders
        for category in self.COMPETITION_CATEGORIES.keys():
            (self.output_dir / category).mkdir(exist_ok=True)

    def load_metadata(self):
        """Load scraping history"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {'categories': {}}
        return {'categories': {}}

    def save_metadata(self):
        """Save scraping history"""
        self.metadata['last_update'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def should_update_category(self, category_key, category_info):
        """
        Determine if category needs updating based on:
        1. Last scrape time
        2. Update frequency
        3. Force update flag
        """
        if category_key not in self.metadata['categories']:
            # Never scraped before - must update
            return True, "never_scraped"

        cat_meta = self.metadata['categories'][category_key]
        last_scrape = datetime.fromisoformat(cat_meta['last_scrape'])
        days_since = (datetime.now() - last_scrape).days

        # Check based on update frequency
        frequency = category_info['update_frequency']

        if frequency == 'daily' and days_since >= 1:
            return True, f"daily_update (last: {days_since}d ago)"
        elif frequency == 'weekly' and days_since >= 7:
            return True, f"weekly_update (last: {days_since}d ago)"
        elif frequency == 'monthly' and days_since >= 30:
            return True, f"monthly_update (last: {days_since}d ago)"

        # Always check if within lookback window (for corrections)
        if days_since <= self.lookback_days:
            return True, f"lookback_check (within {self.lookback_days}d)"

        return False, f"fresh (last: {days_since}d ago)"

    def hash_dataframe(self, df):
        """Generate hash of dataframe content for change detection"""
        # Sort to ensure consistent ordering
        df_sorted = df.sort_values(by=df.columns.tolist()).reset_index(drop=True)
        content = df_sorted.to_csv(index=False)
        return hashlib.md5(content.encode()).hexdigest()

    def detect_changes(self, new_df, category_key):
        """
        Detect what changed compared to previous scrape
        Returns: (is_changed, change_summary)
        """
        # Find latest previous file
        prev_files = list((self.output_dir / category_key).glob("*.csv"))
        if not prev_files:
            return True, {'type': 'new_data', 'details': 'No previous data'}

        # Get most recent file
        latest = max(prev_files, key=lambda p: p.stat().st_mtime)

        try:
            prev_df = pd.read_csv(latest, encoding='utf-8-sig')

            # Quick hash comparison
            new_hash = self.hash_dataframe(new_df)
            prev_hash = self.hash_dataframe(prev_df)

            if new_hash == prev_hash:
                return False, {'type': 'unchanged', 'details': 'Identical data'}

            # Detailed change detection
            changes = {
                'type': 'changed',
                'details': {}
            }

            # Row count change
            if len(new_df) != len(prev_df):
                changes['details']['row_count'] = {
                    'old': len(prev_df),
                    'new': len(new_df),
                    'delta': len(new_df) - len(prev_df)
                }

            # For rankings, detect specific athlete changes
            if 'RANK' in new_df.columns and 'NAME' in new_df.columns:
                changes['details']['ranking_changes'] = self.detect_ranking_changes(prev_df, new_df)

            return True, changes

        except Exception as e:
            return True, {'type': 'error', 'details': f'Could not compare: {e}'}

    def detect_ranking_changes(self, prev_df, new_df):
        """Detect specific ranking changes for athletes"""
        changes = {
            'new_entries': [],
            'dropped_entries': [],
            'rank_changes': [],
            'points_changes': []
        }

        # Create lookup by athlete name
        prev_athletes = {row['NAME']: row for _, row in prev_df.iterrows() if 'NAME' in row}
        new_athletes = {row['NAME']: row for _, row in new_df.iterrows() if 'NAME' in row}

        # Find new athletes
        for name in set(new_athletes.keys()) - set(prev_athletes.keys()):
            changes['new_entries'].append({
                'name': name,
                'rank': new_athletes[name].get('RANK', 'N/A')
            })

        # Find dropped athletes
        for name in set(prev_athletes.keys()) - set(new_athletes.keys()):
            changes['dropped_entries'].append({
                'name': name,
                'prev_rank': prev_athletes[name].get('RANK', 'N/A')
            })

        # Find rank/points changes
        for name in set(prev_athletes.keys()) & set(new_athletes.keys()):
            prev = prev_athletes[name]
            new = new_athletes[name]

            # Rank change
            if 'RANK' in prev and 'RANK' in new:
                prev_rank = prev['RANK']
                new_rank = new['RANK']
                if prev_rank != new_rank:
                    changes['rank_changes'].append({
                        'name': name,
                        'old_rank': prev_rank,
                        'new_rank': new_rank,
                        'change': int(prev_rank) - int(new_rank) if str(prev_rank).isdigit() else 0
                    })

            # Points change
            if 'POINTS' in prev and 'POINTS' in new:
                prev_pts = prev['POINTS']
                new_pts = new['POINTS']
                if prev_pts != new_pts:
                    changes['points_changes'].append({
                        'name': name,
                        'old_points': prev_pts,
                        'new_points': new_pts,
                        'change': float(new_pts) - float(prev_pts) if isinstance(new_pts, (int, float)) else 0
                    })

        # Limit to top changes
        changes['rank_changes'] = sorted(
            changes['rank_changes'],
            key=lambda x: abs(x.get('change', 0)),
            reverse=True
        )[:10]

        return changes

    def setup_driver(self):
        """Setup Chrome"""
        print("\n[AGENT] Initializing Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            print("  ✓ Driver ready")
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def adaptive_wait(self, max_wait=15, check_interval=2):
        """Wait for content with periodic checks"""
        start = time.time()
        while (time.time() - start) < max_wait:
            time.sleep(check_interval)
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            if tables:
                return True, int(time.time() - start)
        return False, max_wait

    def extract_table_smart(self, table_element):
        """Extract table with fallback methods"""
        try:
            from io import StringIO
            html = table_element.get_attribute('outerHTML')
            dfs = pd.read_html(StringIO(html))
            if dfs and len(dfs[0]) > 0:
                return dfs[0]
        except:
            pass

        try:
            headers = [th.text.strip() for th in table_element.find_elements(By.TAG_NAME, 'th')]
            rows_data = []
            for row in table_element.find_elements(By.TAG_NAME, 'tr'):
                cells = [td.text.strip() for td in row.find_elements(By.TAG_NAME, 'td')]
                if cells and any(cells):
                    rows_data.append(cells)

            if rows_data:
                if not headers:
                    headers = [f'Column_{i}' for i in range(len(rows_data[0]))]
                return pd.DataFrame(rows_data, columns=headers)
        except:
            pass

        return None

    def scrape_category_incremental(self, category_key, category_info):
        """
        Scrape category with smart incremental logic
        """
        print("\n" + "="*70)
        print(f"[CHECKING] {category_info['name']}")
        print("="*70)

        # Check if update needed
        should_update, reason = self.should_update_category(category_key, category_info)
        self.stats['categories_checked'] += 1

        if not should_update:
            print(f"\n  ⏭️  SKIPPED: {reason}")
            self.stats['categories_skipped'] += 1
            self.stats['unchanged_categories'].append(category_key)
            return None

        print(f"\n  ✓ UPDATE NEEDED: {reason}")

        # Scrape the data
        url = category_info['url']
        print(f"\n[LOADING] {url}")

        try:
            self.driver.get(url)

            # Handle iframe if needed
            if category_info.get('has_iframe'):
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    src = iframe.get_attribute('src') or ""
                    if 'simplycompete' in src.lower():
                        self.driver.switch_to.frame(iframe)
                        print("  ✓ Switched to rankings iframe")
                        break

            # Adaptive wait
            success, wait_time = self.adaptive_wait()
            print(f"  Content ready after {wait_time}s")

            # Extract tables
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            print(f"  Found {len(tables)} table(s)")

            new_data = None
            for i, table in enumerate(tables):
                df = self.extract_table_smart(table)
                if df is not None and len(df) > 1:
                    new_data = df
                    break

            # Switch back from iframe
            if category_info.get('has_iframe'):
                self.driver.switch_to.default_content()

            if new_data is None:
                print("\n  ⚠️  No data extracted")
                return None

            # Detect changes
            print(f"\n[COMPARING] with previous data...")
            is_changed, change_info = self.detect_changes(new_data, category_key)

            if not is_changed:
                print(f"  ✓ NO CHANGES: {change_info['details']}")
                print("  Skipping save - data unchanged")

                # Update metadata but don't save file
                self.metadata['categories'][category_key] = {
                    'last_scrape': datetime.now().isoformat(),
                    'last_change': self.metadata['categories'].get(category_key, {}).get('last_change'),
                    'status': 'unchanged'
                }
                return None

            # Data changed - save it
            print(f"\n  🔄 CHANGES DETECTED:")
            if 'row_count' in change_info.get('details', {}):
                rc = change_info['details']['row_count']
                print(f"    Rows: {rc['old']} → {rc['new']} ({rc['delta']:+d})")

            if 'ranking_changes' in change_info.get('details', {}):
                rc = change_info['details']['ranking_changes']
                if rc['new_entries']:
                    print(f"    New athletes: {len(rc['new_entries'])}")
                if rc['rank_changes']:
                    print(f"    Rank changes: {len(rc['rank_changes'])}")
                    for change in rc['rank_changes'][:3]:  # Top 3
                        print(f"      • {change['name']}: #{change['old_rank']} → #{change['new_rank']}")

            # Save new data
            filename = f"{category_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self.output_dir / category_key / filename

            new_data.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"\n  ✓ SAVED: {filename} ({len(new_data)} rows)")

            # Update metadata
            self.metadata['categories'][category_key] = {
                'last_scrape': datetime.now().isoformat(),
                'last_change': datetime.now().isoformat(),
                'rows': len(new_data),
                'file': str(filepath),
                'status': 'updated'
            }

            self.stats['categories_updated'] += 1
            self.stats['new_data_rows'] += len(new_data)
            self.stats['changes_detected'].append({
                'category': category_key,
                'change_info': change_info
            })

            return new_data

        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            return None

    def run_incremental_update(self):
        """Main incremental update operation"""
        print("="*70)
        print("INCREMENTAL TAEKWONDO SCRAPER")
        print(f"Smart Updates (lookback: {self.lookback_days} days)")
        print("="*70)

        if not self.setup_driver():
            return None

        try:
            # Sort by priority
            sorted_categories = sorted(
                self.COMPETITION_CATEGORIES.items(),
                key=lambda x: x[1]['priority']
            )

            # Check each category
            for category_key, category_info in sorted_categories:
                self.scrape_category_incremental(category_key, category_info)
                time.sleep(2)

            # Save metadata
            self.save_metadata()

            # Generate report
            self.generate_report()

        except KeyboardInterrupt:
            print("\n\n[INTERRUPTED]")
            self.save_metadata()
            self.generate_report()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                self.driver.quit()
                print("\n[CLEANUP] Browser closed")

    def generate_report(self):
        """Generate update report"""
        print("\n" + "="*70)
        print("[UPDATE REPORT]")
        print("="*70)

        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds() / 60

        print(f"\nRuntime: {elapsed:.1f} minutes")
        print(f"Categories checked: {self.stats['categories_checked']}")
        print(f"Categories updated: {self.stats['categories_updated']}")
        print(f"Categories skipped: {self.stats['categories_skipped']}")
        print(f"New data rows: {self.stats['new_data_rows']}")

        if self.stats['unchanged_categories']:
            print(f"\n[SKIPPED] {len(self.stats['unchanged_categories'])} unchanged:")
            for cat in self.stats['unchanged_categories']:
                print(f"  • {cat}")

        if self.stats['changes_detected']:
            print(f"\n[CHANGES] {len(self.stats['changes_detected'])} categories updated:")
            for change in self.stats['changes_detected']:
                print(f"  • {change['category']}")

        # Save report
        self.stats['end_time'] = datetime.now().isoformat()
        report_file = self.output_dir / f"update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Report: {report_file}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Incremental Taekwondo Web Scraping Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Smart Incremental Updates:
  ✓ Only scrapes changed data
  ✓ Checks back 30 days for corrections (configurable)
  ✓ Detects ranking changes automatically
  ✓ Skips unchanged categories
  ✓ Daily/weekly/monthly update schedules per category

Update Frequencies:
  - Rankings: Daily (if changed)
  - Olympics: Monthly (rarely changes)
  - World Championships: Weekly (new events added)

Examples:
  # Daily update (default 30-day lookback)
  python scraper_agent_incremental.py

  # Shorter lookback (7 days)
  python scraper_agent_incremental.py --lookback 7

  # Longer lookback (60 days)
  python scraper_agent_incremental.py --lookback 60

  # Visible browser (debugging)
  python scraper_agent_incremental.py --visible
        """
    )

    parser.add_argument('--lookback', type=int, default=30,
                        help='Days to look back for corrections (default: 30)')
    parser.add_argument('--visible', action='store_true',
                        help='Run with visible browser')
    parser.add_argument('--output', default='data_incremental',
                        help='Output directory (default: data_incremental)')

    args = parser.parse_args()

    try:
        agent = IncrementalScraperAgent(
            output_dir=args.output,
            lookback_days=args.lookback,
            headless=not args.visible
        )

        agent.run_incremental_update()

        print(f"\n✓ Update complete!")
        print(f"  Updated: {agent.stats['categories_updated']} categories")
        print(f"  Skipped: {agent.stats['categories_skipped']} unchanged")
        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED]")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    exit(main())
