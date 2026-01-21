"""
Comprehensive scraper for worldtkd.simplycompete.com
Gets all competition data including Olympics, World Championships, Grand Prix, etc.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

class SimplyCompeteScraper:
    def __init__(self, output_dir="data_simplycompete"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://worldtkd.simplycompete.com"

        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        # Run in visible mode to see what's happening
        # self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')

        self.competitions = []
        self.all_matches = []

    def find_competitions(self, driver):
        """Find all available competitions on the site"""
        print(f"\n{'='*70}")
        print("FINDING COMPETITIONS")
        print(f"{'='*70}")

        try:
            driver.get(self.base_url)
            print(f"\n[LOADING] {self.base_url}")
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save main page
            with open(self.output_dir / "main_page.html", 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            # Look for competition links
            # Check for various patterns
            patterns = [
                ('a[href*="event"]', 'Event links'),
                ('a[href*="competition"]', 'Competition links'),
                ('.competition-item', 'Competition items'),
                ('.event-card', 'Event cards'),
            ]

            found_links = []
            for selector, desc in patterns:
                elements = soup.select(selector)
                if elements:
                    print(f"\n  Found {len(elements)} {desc}")
                    for elem in elements[:10]:  # Show first 10
                        href = elem.get('href', '')
                        text = elem.get_text(strip=True)
                        if href and len(text) > 0:
                            print(f"    - {text[:60]} -> {href[:80]}")
                            found_links.append({'url': href, 'name': text})

            # Look for text mentioning competitions
            keywords = ['olympic', 'world championship', 'grand prix', 'grand slam',
                       'paris 2024', 'tokyo 2020']

            for keyword in keywords:
                elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if elements:
                    print(f"\n  Found '{keyword}': {len(elements)} references")
                    for elem in elements[:3]:
                        try:
                            text = elem.text.strip()
                            if len(text) > 0 and len(text) < 200:
                                print(f"    - {text}")

                                # Try to find parent link
                                try:
                                    parent_link = elem.find_element(By.XPATH, "./ancestor::a")
                                    href = parent_link.get_attribute('href')
                                    if href:
                                        found_links.append({'url': href, 'name': text})
                                except:
                                    pass
                        except:
                            pass

            # Try clicking through navigation
            nav_items = driver.find_elements(By.CSS_SELECTOR, "nav a, .nav-link, .menu-item")
            if nav_items:
                print(f"\n  Found {len(nav_items)} navigation items")

            self.competitions = found_links
            return found_links

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_competition(self, driver, comp_url, comp_name):
        """Scrape all data from a competition"""
        print(f"\n{'='*70}")
        print(f"SCRAPING: {comp_name}")
        print(f"{'='*70}")
        print(f"URL: {comp_url}")

        try:
            # Make URL absolute
            if not comp_url.startswith('http'):
                comp_url = self.base_url + comp_url

            driver.get(comp_url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save competition page
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', comp_name)[:50]
            comp_file = self.output_dir / f"comp_{safe_name}.html"
            with open(comp_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"  Saved: {comp_file.name}")

            # Extract match results
            matches = self.extract_matches(soup, comp_name)

            if matches:
                print(f"  Found {len(matches)} matches")
                self.all_matches.extend(matches)

                # Save competition matches
                matches_file = self.output_dir / f"matches_{safe_name}.json"
                with open(matches_file, 'w', encoding='utf-8') as f:
                    json.dump(matches, f, indent=2)
                print(f"  Saved: {matches_file.name}")
            else:
                print("  No matches found")

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    def extract_matches(self, soup, comp_name):
        """Extract match data from competition page"""
        matches = []

        # Look for match result patterns
        # Pattern 1: Table rows
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Likely a match row
                    match_data = {
                        'competition': comp_name,
                        'row_text': row.get_text(' | ', strip=True),
                        'cells': [cell.get_text(strip=True) for cell in cells]
                    }

                    # Look for weight category
                    for cell in cells:
                        text = cell.get_text()
                        if 'kg' in text.lower():
                            match_data['weight'] = text

                    # Look for countries (3-letter codes)
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if len(text) == 3 and text.isupper():
                            if 'country1' not in match_data:
                                match_data['country1'] = text
                            elif text != match_data['country1']:
                                match_data['country2'] = text

                    # Look for View buttons
                    view_links = row.find_all(['a', 'button'], text=lambda t: t and 'view' in str(t).lower())
                    if view_links:
                        for link in view_links:
                            href = link.get('href')
                            if href:
                                match_data['view_url'] = href

                    matches.append(match_data)

        # Pattern 2: Divs with match class
        match_divs = soup.find_all(['div', 'article'], class_=lambda c: c and any(
            x in str(c).lower() for x in ['match', 'result', 'bout']))

        for div in match_divs:
            match_data = {
                'competition': comp_name,
                'div_text': div.get_text(' | ', strip=True)
            }

            # Extract countries and scores
            text = div.get_text()
            countries = re.findall(r'\b[A-Z]{3}\b', text)
            if len(countries) >= 2:
                match_data['country1'] = countries[0]
                match_data['country2'] = countries[1]

            # Extract scores (pattern like "2:0" or "2-1")
            scores = re.findall(r'(\d+)[:-](\d+)', text)
            if scores:
                match_data['score'] = scores[0]

            matches.append(match_data)

        return matches

    def scrape_all(self):
        """Main scraping function"""
        print("="*70)
        print("SIMPLY COMPETE COMPREHENSIVE SCRAPER")
        print("="*70)

        driver = webdriver.Chrome(options=self.options)

        try:
            # Find all competitions
            competitions = self.find_competitions(driver)

            if not competitions:
                print("\n[WARNING] No competitions found!")
                print("The site may require login or have different structure.")
                print("Saving page for manual inspection...")
                return

            print(f"\n[FOUND] {len(competitions)} competitions")

            # Scrape each competition
            for idx, comp in enumerate(competitions[:10], 1):  # Limit to first 10
                print(f"\n[{idx}/{min(len(competitions), 10)}]")
                self.scrape_competition(driver, comp['url'], comp['name'])
                time.sleep(2)  # Be nice to the server

        finally:
            driver.quit()

        print(f"\n{'='*70}")
        print("SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Total matches: {len(self.all_matches)}")

    def save_summary(self):
        """Save summary and combined data"""
        print(f"\n[SAVING] Summary to {self.output_dir}")

        # Save all matches
        if self.all_matches:
            all_matches_file = self.output_dir / "all_matches.json"
            with open(all_matches_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_matches, f, indent=2)
            print(f"  Saved {len(self.all_matches)} matches to {all_matches_file.name}")

            # Try to create CSV
            try:
                csv_data = []
                for match in self.all_matches:
                    csv_row = {
                        'competition': match.get('competition', ''),
                        'country1': match.get('country1', ''),
                        'country2': match.get('country2', ''),
                        'weight': match.get('weight', ''),
                        'score': match.get('score', ''),
                        'has_view_url': 'view_url' in match
                    }
                    csv_data.append(csv_row)

                if csv_data:
                    df = pd.DataFrame(csv_data)
                    csv_file = self.output_dir / "all_matches.csv"
                    df.to_csv(csv_file, index=False, encoding='utf-8')
                    print(f"  Saved CSV: {csv_file.name}")
            except Exception as e:
                print(f"  Could not create CSV: {e}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'competitions_found': len(self.competitions),
            'total_matches': len(self.all_matches),
            'competitions': self.competitions[:20],  # First 20
            'output_directory': str(self.output_dir)
        }

        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved summary: {summary_file.name}")

def main():
    scraper = SimplyCompeteScraper()

    try:
        scraper.scrape_all()
        scraper.save_summary()

        print(f"\n[COMPLETE] Check {scraper.output_dir} for all data")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        scraper.save_summary()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
