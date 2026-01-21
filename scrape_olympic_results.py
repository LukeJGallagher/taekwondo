"""
Scrape Olympic Taekwondo Results with detailed match data
Gets results from simplycompete.com or World Taekwondo results system
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

class OlympicResultsScraper:
    def __init__(self, output_dir="data_all_categories/olympics_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Try multiple possible URLs for Olympic results
        self.olympic_urls = [
            "https://worldtkd.simplycompete.com",
            "https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents",
            "https://www.worldtaekwondo.org/competitions/results"
        ]

        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')

        self.match_results = []
        self.detailed_matches = []

    def scrape_match_list(self, driver, url):
        """Scrape list of matches from results page"""
        print(f"\n[SCRAPING] {url}")

        try:
            driver.get(url)
            time.sleep(5)  # Wait for page load

            # Get page source
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Look for match result containers
            matches = []

            # Try different selectors for match data
            selectors = [
                ('.match-result', 'match result divs'),
                ('.result-row', 'result rows'),
                ('tr[data-match]', 'match table rows'),
                ('.competition-match', 'competition matches')
            ]

            for selector, desc in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"  Found {len(elements)} {desc}")

                    for elem in elements:
                        match_data = {
                            'html': str(elem),
                            'text': elem.get_text(strip=True)
                        }

                        # Look for View buttons/links
                        view_links = elem.find_all(['a', 'button'], text=lambda t: t and 'view' in t.lower())
                        if view_links:
                            for link in view_links:
                                href = link.get('href') or link.get('onclick', '')
                                if href:
                                    match_data['view_link'] = href

                        matches.append(match_data)

            # Also try to find weight categories
            weight_elements = soup.find_all(text=lambda t: t and 'kg' in t.lower())
            print(f"  Found {len(weight_elements)} weight category references")

            return matches

        except Exception as e:
            print(f"  [ERROR] {e}")
            return []

    def extract_match_details(self, driver, match_url):
        """Click View button and extract detailed match data"""
        try:
            print(f"\n  [DETAIL] Loading match details...")
            driver.get(match_url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract all text and tables
            match_detail = {
                'url': match_url,
                'timestamp': datetime.now().isoformat(),
                'text': soup.get_text(separator='\n', strip=True)
            }

            # Look for score tables
            tables = soup.find_all('table')
            if tables:
                match_detail['tables'] = []
                for idx, table in enumerate(tables):
                    try:
                        df = pd.read_html(str(table))[0]
                        match_detail['tables'].append(df.to_dict())
                    except:
                        pass

            return match_detail

        except Exception as e:
            print(f"    [ERROR] {e}")
            return None

    def scrape_olympics(self):
        """Main scraping function"""
        print("="*70)
        print("OLYMPIC RESULTS SCRAPER")
        print("="*70)

        driver = webdriver.Chrome(options=self.options)

        try:
            for url in self.olympic_urls:
                print(f"\n[TRYING] {url}")

                try:
                    driver.get(url)
                    time.sleep(5)

                    # Save page HTML
                    page_html = driver.page_source
                    html_file = self.output_dir / f"page_{url.replace('://', '_').replace('/', '_')}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    print(f"  Saved: {html_file.name}")

                    # Check for match results
                    soup = BeautifulSoup(page_html, 'html.parser')

                    # Look for any text mentioning Olympics, weight categories, or match results
                    keywords = ['olympic', 'paris 2024', 'tokyo 2020', '-58kg', '-68kg',
                               'final', 'quarterfinal', 'match result']

                    found_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in page_html.lower():
                            found_keywords.append(keyword)

                    if found_keywords:
                        print(f"  Found keywords: {', '.join(found_keywords)}")

                        # This page has Olympic data, scrape it
                        matches = self.scrape_match_list(driver, url)

                        if matches:
                            print(f"\n[FOUND] {len(matches)} matches")

                            # Save match list
                            matches_file = self.output_dir / f"matches_list_{len(self.match_results)}.json"
                            with open(matches_file, 'w', encoding='utf-8') as f:
                                json.dump(matches, f, indent=2)
                            print(f"  Saved: {matches_file}")

                            self.match_results.extend(matches)

                            # Try to get detailed data from first few matches
                            for i, match in enumerate(matches[:5]):  # Limit to first 5
                                if 'view_link' in match:
                                    print(f"\n  [MATCH {i+1}] Getting details...")
                                    detail = self.extract_match_details(driver, match['view_link'])
                                    if detail:
                                        self.detailed_matches.append(detail)
                    else:
                        print("  No Olympic data found on this page")

                except Exception as e:
                    print(f"  [ERROR] Failed to load {url}: {e}")
                    continue

        finally:
            driver.quit()

        print(f"\n{'='*70}")
        print("SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Matches found: {len(self.match_results)}")
        print(f"Detailed matches: {len(self.detailed_matches)}")

    def save_results(self):
        """Save all scraped data"""
        print(f"\n[SAVING] Results to {self.output_dir}")

        # Save match results
        if self.match_results:
            results_file = self.output_dir / "olympic_matches.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.match_results, f, indent=2)
            print(f"  Saved {len(self.match_results)} matches to {results_file.name}")

        # Save detailed matches
        if self.detailed_matches:
            details_file = self.output_dir / "olympic_match_details.json"
            with open(details_file, 'w', encoding='utf-8') as f:
                json.dump(self.detailed_matches, f, indent=2)
            print(f"  Saved {len(self.detailed_matches)} detailed matches to {details_file.name}")

            # Try to create CSV
            try:
                # Extract basic info for CSV
                csv_data = []
                for match in self.match_results:
                    text = match.get('text', '')
                    csv_data.append({
                        'match_text': text[:200],  # First 200 chars
                        'has_view_link': 'view_link' in match
                    })

                if csv_data:
                    df = pd.DataFrame(csv_data)
                    csv_file = self.output_dir / "olympic_matches.csv"
                    df.to_csv(csv_file, index=False, encoding='utf-8')
                    print(f"  Saved CSV: {csv_file.name}")
            except Exception as e:
                print(f"  Could not create CSV: {e}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_matches': len(self.match_results),
            'detailed_matches': len(self.detailed_matches),
            'output_directory': str(self.output_dir)
        }

        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved summary: {summary_file.name}")

def main():
    print("\nNOTE: If you have a specific Olympic results URL, please provide it!")
    print("Common URLs:")
    print("  - https://worldtkd.simplycompete.com/events/[event_id]")
    print("  - https://www.worldtaekwondo.org/competitions/[competition_id]")
    print()

    scraper = OlympicResultsScraper()

    try:
        scraper.scrape_olympics()
        scraper.save_results()

        print(f"\n[COMPLETE] Check {scraper.output_dir} for results")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        scraper.save_results()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
