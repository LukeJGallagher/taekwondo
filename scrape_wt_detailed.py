"""
Enhanced World Taekwondo API Scraper
Scrapes detailed competition data from web.worldtaekwondo.martial.services
Focuses on major competitions: Olympics, World Championships, Grand Prix
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

class WorldTaekwondoDetailedScraper:
    def __init__(self, output_dir="data_wt_detailed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://web.worldtaekwondo.martial.services"
        self.competitions = []
        self.all_results = []

    def setup_driver(self):
        """Setup headless Chrome"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        return webdriver.Chrome(options=options)

    def extract_unique_competitions(self):
        """Extract unique competition slugs from the competitions list CSV"""
        print(f"\n{'='*70}")
        print("EXTRACTING UNIQUE COMPETITIONS")
        print(f"{'='*70}")

        csv_file = Path("data_wt_api/competitions_list.csv")
        if not csv_file.exists():
            print(f"[ERROR] {csv_file} not found!")
            return []

        df = pd.read_csv(csv_file)
        print(f"\nTotal rows in CSV: {len(df)}")

        # Extract competition slugs from URLs
        competitions = []
        seen_slugs = set()

        for _, row in df.iterrows():
            url = row['url']
            # Extract competition slug from URL
            # Pattern: /competitions/{slug}/results or /competitions/{slug}/medalists
            match = re.search(r'/competitions/([^/]+)/(results|medalists)', url)
            if match:
                slug = match.group(1)
                if slug not in seen_slugs:
                    seen_slugs.add(slug)

                    # Determine competition type and priority
                    priority = self.get_competition_priority(slug)

                    comp_data = {
                        'slug': slug,
                        'name': slug.replace('-', ' ').title(),
                        'priority': priority,
                        'results_url': f"{self.base_url}/competitions/{slug}/results",
                        'medalists_url': f"{self.base_url}/competitions/{slug}/medalists"
                    }
                    competitions.append(comp_data)

        # Sort by priority (higher priority first)
        competitions.sort(key=lambda x: x['priority'], reverse=True)

        print(f"\n[EXTRACTED] {len(competitions)} unique competitions")

        # Show top priorities
        print("\n[TOP PRIORITY COMPETITIONS]")
        for comp in competitions[:20]:
            print(f"  Priority {comp['priority']}: {comp['name']}")

        self.competitions = competitions
        return competitions

    def get_competition_priority(self, slug):
        """Assign priority to competitions (higher = more important)"""
        slug_lower = slug.lower()

        # Highest priority: Olympics
        if 'olympic' in slug_lower or 'og' in slug_lower:
            if '2024' in slug_lower or 'paris' in slug_lower:
                return 1000
            elif '2020' in slug_lower or 'tokyo' in slug_lower:
                return 950
            elif '2016' in slug_lower or 'rio' in slug_lower:
                return 900
            elif '2012' in slug_lower or 'london' in slug_lower:
                return 850
            elif '2008' in slug_lower or 'beijing' in slug_lower:
                return 800
            else:
                return 750

        # High priority: World Championships
        if 'world' in slug_lower and 'championships' in slug_lower:
            # Extract year
            year_match = re.search(r'(202[0-9]|201[0-9])', slug_lower)
            if year_match:
                year = int(year_match.group(1))
                return 700 + (year - 2000)  # More recent = higher priority
            return 700

        # Medium-high priority: Grand Prix/Grand Slam
        if 'grand-prix' in slug_lower or 'grand-slam' in slug_lower:
            year_match = re.search(r'(202[0-9]|201[0-9])', slug_lower)
            if year_match:
                year = int(year_match.group(1))
                return 600 + (year - 2000)
            return 600

        # Medium priority: Continental championships
        if any(x in slug_lower for x in ['european', 'asian', 'pan-am', 'african']):
            return 400

        # Lower priority: Open tournaments
        if 'open' in slug_lower:
            return 200

        # Default priority
        return 100

    def scrape_competition_results(self, driver, comp):
        """Scrape detailed results for a competition"""
        print(f"\n{'='*70}")
        print(f"SCRAPING: {comp['name']}")
        print(f"Priority: {comp['priority']}")
        print(f"{'='*70}")

        comp_data = {
            'slug': comp['slug'],
            'name': comp['name'],
            'priority': comp['priority'],
            'results': [],
            'medalists': [],
            'result_book_pdf': None
        }

        # 1. Get results page
        try:
            print(f"\n[RESULTS] {comp['results_url']}")
            driver.get(comp['results_url'])
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save HTML
            html_file = self.output_dir / f"{comp['slug']}_results.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"  Saved HTML: {html_file.name}")

            # Extract results tables
            tables = soup.find_all('table')
            print(f"  Found {len(tables)} tables")

            for idx, table in enumerate(tables):
                try:
                    # Parse table with pandas
                    df = pd.read_html(str(table))[0]

                    # Save individual table
                    table_csv = self.output_dir / f"{comp['slug']}_results_table_{idx}.csv"
                    df.to_csv(table_csv, index=False, encoding='utf-8')

                    comp_data['results'].append({
                        'table_index': idx,
                        'rows': len(df),
                        'columns': list(df.columns),
                        'csv_file': table_csv.name
                    })
                    print(f"  Table {idx}: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    print(f"  [ERROR] Table {idx}: {e}")

            # Look for result book PDF link
            pdf_links = soup.find_all('a', href=lambda h: h and '.pdf' in h.lower())
            if pdf_links:
                for link in pdf_links:
                    href = link.get('href')
                    if 'resultbook' in href.lower() or 'result-book' in href.lower():
                        comp_data['result_book_pdf'] = href
                        print(f"  Found result book PDF: {href}")
                        break

        except Exception as e:
            print(f"[ERROR] Results: {e}")

        # 2. Get medalists page
        try:
            print(f"\n[MEDALISTS] {comp['medalists_url']}")
            driver.get(comp['medalists_url'])
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Save HTML
            html_file = self.output_dir / f"{comp['slug']}_medalists.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"  Saved HTML: {html_file.name}")

            # Extract medalists tables
            tables = soup.find_all('table')
            print(f"  Found {len(tables)} tables")

            for idx, table in enumerate(tables):
                try:
                    df = pd.read_html(str(table))[0]

                    # Save individual table
                    table_csv = self.output_dir / f"{comp['slug']}_medalists_table_{idx}.csv"
                    df.to_csv(table_csv, index=False, encoding='utf-8')

                    comp_data['medalists'].append({
                        'table_index': idx,
                        'rows': len(df),
                        'columns': list(df.columns),
                        'csv_file': table_csv.name
                    })
                    print(f"  Table {idx}: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    print(f"  [ERROR] Table {idx}: {e}")

        except Exception as e:
            print(f"[ERROR] Medalists: {e}")

        # Save competition data JSON
        json_file = self.output_dir / f"{comp['slug']}_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comp_data, f, indent=2)
        print(f"\n[SAVED] {json_file.name}")

        self.all_results.append(comp_data)
        return comp_data

    def download_result_books(self):
        """Download result book PDFs for competitions that have them"""
        print(f"\n{'='*70}")
        print("DOWNLOADING RESULT BOOKS")
        print(f"{'='*70}")

        pdf_dir = self.output_dir / "result_books"
        pdf_dir.mkdir(exist_ok=True)

        downloaded = 0
        for comp_data in self.all_results:
            if comp_data.get('result_book_pdf'):
                pdf_url = comp_data['result_book_pdf']
                if not pdf_url.startswith('http'):
                    pdf_url = self.base_url + pdf_url

                pdf_filename = pdf_dir / f"{comp_data['slug']}_result_book.pdf"

                try:
                    print(f"\n[DOWNLOADING] {comp_data['name']}")
                    print(f"  URL: {pdf_url}")

                    response = requests.get(pdf_url, timeout=30)
                    if response.status_code == 200:
                        with open(pdf_filename, 'wb') as f:
                            f.write(response.content)

                        size_mb = len(response.content) / (1024 * 1024)
                        print(f"  Saved: {pdf_filename.name} ({size_mb:.2f} MB)")
                        downloaded += 1
                    else:
                        print(f"  [ERROR] Status {response.status_code}")
                except Exception as e:
                    print(f"  [ERROR] {e}")

        print(f"\n[COMPLETE] Downloaded {downloaded} result books")

    def scrape_all(self, max_competitions=50):
        """Main scraping function"""
        print("="*70)
        print("WORLD TAEKWONDO DETAILED SCRAPER")
        print("="*70)

        # Extract unique competitions
        competitions = self.extract_unique_competitions()

        if not competitions:
            print("[ERROR] No competitions found!")
            return

        driver = self.setup_driver()

        try:
            # Scrape top priority competitions
            scrape_count = min(max_competitions, len(competitions))
            print(f"\n[SCRAPING] Top {scrape_count} competitions by priority...")

            for idx, comp in enumerate(competitions[:scrape_count], 1):
                print(f"\n[{idx}/{scrape_count}]")
                self.scrape_competition_results(driver, comp)
                time.sleep(2)  # Be nice to the server

        finally:
            driver.quit()

        print(f"\n{'='*70}")
        print("SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Competitions scraped: {len(self.all_results)}")

    def save_summary(self):
        """Save comprehensive summary"""
        print(f"\n[SAVING] Summary to {self.output_dir}")

        # Create summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_competitions_scraped': len(self.all_results),
            'total_unique_competitions': len(self.competitions),
            'competitions': []
        }

        for comp in self.all_results:
            summary['competitions'].append({
                'name': comp['name'],
                'slug': comp['slug'],
                'priority': comp['priority'],
                'results_tables': len(comp['results']),
                'medalists_tables': len(comp['medalists']),
                'has_result_book': comp['result_book_pdf'] is not None
            })

        # Save summary JSON
        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved: {summary_file.name}")

        # Create master CSV of all competitions
        if self.competitions:
            df = pd.DataFrame(self.competitions)
            csv_file = self.output_dir / "all_competitions_prioritized.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"  Saved: {csv_file.name} ({len(df)} competitions)")

def main():
    print("\n" + "="*70)
    print("World Taekwondo Detailed Scraper")
    print("Scraping Olympics, World Championships, and Grand Prix competitions")
    print("="*70 + "\n")

    scraper = WorldTaekwondoDetailedScraper()

    try:
        # Scrape top 50 competitions (includes all Olympics and recent major events)
        scraper.scrape_all(max_competitions=50)

        # Download result book PDFs
        scraper.download_result_books()

        # Save summary
        scraper.save_summary()

        print(f"\n[SUCCESS] Check {scraper.output_dir.absolute()} for all data")
        print("\nData saved:")
        print("  - Individual competition HTML files")
        print("  - Results and medalists tables as CSV")
        print("  - Competition data as JSON")
        print("  - Result book PDFs (if available)")
        print("  - Comprehensive summary")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        scraper.save_summary()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
