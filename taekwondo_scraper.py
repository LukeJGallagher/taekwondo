"""
Advanced Taekwondo Data Scraper
Scrapes comprehensive competition results, athlete profiles, and rankings from World Taekwondo
Focus: Getting detailed match data for performance analysis
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaekwondoDataScraper:
    """Comprehensive scraper for World Taekwondo data"""

    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "competitions").mkdir(exist_ok=True)
        (self.output_dir / "athletes").mkdir(exist_ok=True)
        (self.output_dir / "rankings").mkdir(exist_ok=True)
        (self.output_dir / "matches").mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def get_json_data(self, url: str) -> Optional[Dict]:
        """Fetch JSON data from API endpoints"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    def get_html_data(self, url: str) -> Optional[str]:
        """Fetch HTML data"""
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    def scrape_world_rankings(self) -> pd.DataFrame:
        """
        Scrape current world rankings
        World Taekwondo provides rankings by weight category
        """
        print("\n[1] Scraping World Rankings...")

        # Weight categories
        categories = {
            'M': {'-54kg': '1', '-58kg': '2', '-63kg': '3', '-68kg': '4',
                  '-74kg': '5', '-80kg': '6', '-87kg': '7', '+87kg': '8'},
            'F': {'-46kg': '9', '-49kg': '10', '-53kg': '11', '-57kg': '12',
                  '-62kg': '13', '-67kg': '14', '-73kg': '15', '+73kg': '16'}
        }

        all_rankings = []

        for gender, weights in categories.items():
            for weight, code in weights.items():
                print(f"  Fetching {gender} {weight}...")

                # Try API endpoint (this may need adjustment based on actual API)
                url = f"https://www.worldtaekwondo.org/competition/ranking.html?gender={gender}&weight={code}"
                html = self.get_html_data(url)

                if html:
                    soup = BeautifulSoup(html, 'html.parser')

                    # Parse ranking table (structure may vary)
                    table = soup.find('table', {'class': 'ranking-table'}) or soup.find('table')

                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header

                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 4:
                                ranking_data = {
                                    'rank': cols[0].get_text(strip=True),
                                    'athlete_name': cols[1].get_text(strip=True),
                                    'country': cols[2].get_text(strip=True),
                                    'points': cols[3].get_text(strip=True),
                                    'gender': gender,
                                    'weight_category': weight,
                                    'scraped_date': datetime.now().isoformat()
                                }
                                all_rankings.append(ranking_data)

                time.sleep(0.5)

        df = pd.DataFrame(all_rankings)
        output_file = self.output_dir / "rankings" / f"world_rankings_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(output_file, index=False)
        print(f"  [OK] Saved {len(df)} rankings to {output_file}")

        return df

    def scrape_competition_list(self, year_from: int = 2015, year_to: int = None) -> List[Dict]:
        """
        Scrape list of all competitions in date range
        """
        if year_to is None:
            year_to = datetime.now().year

        print(f"\n[2] Scraping Competitions ({year_from}-{year_to})...")

        competitions = []

        # World Taekwondo competition list URL
        for year in range(year_from, year_to + 1):
            print(f"  Year: {year}")

            # Try multiple endpoints
            urls = [
                f"https://m.worldtaekwondo.org/competition/list.html?year={year}&mcd=A01",
                f"https://www.worldtaekwondo.org/competition/list.html?year={year}",
            ]

            for url in urls:
                html = self.get_html_data(url)

                if html:
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find competition entries
                    comp_items = soup.find_all('div', class_='competition-item') or \
                                soup.find_all('a', href=lambda x: x and 'view.html' in x)

                    for item in comp_items:
                        comp_data = {}

                        # Extract competition ID from URL
                        if item.name == 'a':
                            link = item.get('href', '')
                            if 'gid=' in link:
                                comp_id = link.split('gid=')[1].split('&')[0]
                                comp_data['competition_id'] = comp_id
                                comp_data['url'] = f"https://www.worldtaekwondo.org/competition/view.html?gid={comp_id}"

                        # Extract name and date
                        comp_data['name'] = item.get_text(strip=True)
                        comp_data['year'] = year

                        if comp_data.get('competition_id'):
                            competitions.append(comp_data)

                    break  # If we got data, don't try other URLs

            time.sleep(0.3)

        # Save competition list
        output_file = self.output_dir / "competitions" / f"competition_list_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(competitions, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Found {len(competitions)} competitions")
        return competitions

    def scrape_competition_results(self, competition_id: str) -> Dict:
        """
        Scrape detailed results for a specific competition
        Includes brackets, match results, and athlete performance
        """
        print(f"\n[3] Scraping Competition {competition_id}...")

        base_url = f"https://www.worldtaekwondo.org/competition/view.html?gid={competition_id}"
        html = self.get_html_data(base_url)

        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        competition_data = {
            'competition_id': competition_id,
            'name': '',
            'date': '',
            'location': '',
            'categories': [],
            'matches': []
        }

        # Extract competition details
        title = soup.find('h1') or soup.find('div', class_='title')
        if title:
            competition_data['name'] = title.get_text(strip=True)

        # Look for result links (PDF, brackets, etc.)
        result_links = soup.find_all('a', href=lambda x: x and ('result' in x.lower() or '.pdf' in x))

        # Try to find match data tables
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cols = row.find_all('td')

                # Try to identify match data structure
                if len(cols) >= 3:
                    match_data = {
                        'category': '',
                        'athlete1': '',
                        'athlete1_country': '',
                        'athlete2': '',
                        'athlete2_country': '',
                        'score': '',
                        'winner': '',
                        'round': ''
                    }

                    # Parse based on actual structure (this is a template)
                    if cols[0].get_text(strip=True):
                        match_data['athlete1'] = cols[0].get_text(strip=True)

                    competition_data['matches'].append(match_data)

        # Save competition data
        output_file = self.output_dir / "competitions" / f"competition_{competition_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(competition_data, f, indent=2, ensure_ascii=False)

        return competition_data

    def scrape_athlete_profile(self, athlete_id: str) -> Dict:
        """
        Scrape individual athlete profile and competition history
        """
        print(f"\n[4] Scraping Athlete {athlete_id}...")

        url = f"https://www.worldtaekwondo.org/athlete/view.html?aid={athlete_id}"
        html = self.get_html_data(url)

        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        athlete_data = {
            'athlete_id': athlete_id,
            'name': '',
            'country': '',
            'birth_date': '',
            'weight_category': '',
            'gender': '',
            'competitions': [],
            'medals': {'gold': 0, 'silver': 0, 'bronze': 0}
        }

        # Parse athlete details (structure depends on actual website)
        name_elem = soup.find('h1', class_='athlete-name') or soup.find('h1')
        if name_elem:
            athlete_data['name'] = name_elem.get_text(strip=True)

        # Save athlete data
        output_file = self.output_dir / "athletes" / f"athlete_{athlete_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(athlete_data, f, indent=2, ensure_ascii=False)

        return athlete_data

    def scrape_saudi_athletes(self) -> pd.DataFrame:
        """
        Focus on Saudi Arabian athletes
        Get all Saudi athletes and their complete competition history
        """
        print("\n[5] Scraping Saudi Athletes...")

        # Search for Saudi athletes
        search_url = "https://www.worldtaekwondo.org/athlete/list.html?country=KSA"
        html = self.get_html_data(search_url)

        saudi_athletes = []

        if html:
            soup = BeautifulSoup(html, 'html.parser')

            # Find all athlete links
            athlete_links = soup.find_all('a', href=lambda x: x and 'athlete/view.html' in x)

            for link in athlete_links:
                athlete_id = None
                if 'aid=' in link.get('href', ''):
                    athlete_id = link.get('href').split('aid=')[1].split('&')[0]

                if athlete_id:
                    # Get detailed profile
                    athlete_data = self.scrape_athlete_profile(athlete_id)
                    saudi_athletes.append(athlete_data)
                    time.sleep(0.5)

        df = pd.DataFrame(saudi_athletes)
        output_file = self.output_dir / "athletes" / f"saudi_athletes_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(output_file, index=False)
        print(f"  [OK] Saved {len(df)} Saudi athletes")

        return df

    def run_full_scrape(self, focus_saudi: bool = True):
        """
        Run comprehensive data collection
        """
        print("="*70)
        print("TAEKWONDO DATA SCRAPER - Full Collection")
        print("="*70)

        # 1. Get world rankings
        rankings_df = self.scrape_world_rankings()

        # 2. Get competition list
        competitions = self.scrape_competition_list(year_from=2020)

        # 3. Scrape recent competitions (limit to avoid overwhelming)
        for comp in competitions[:10]:  # Top 10 most recent
            if comp.get('competition_id'):
                self.scrape_competition_results(comp['competition_id'])
                time.sleep(1)

        # 4. Focus on Saudi athletes
        if focus_saudi:
            saudi_df = self.scrape_saudi_athletes()

        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print(f"Data saved to: {self.output_dir.absolute()}")
        print("="*70)


def main():
    scraper = TaekwondoDataScraper(output_dir="data")
    scraper.run_full_scrape(focus_saudi=True)


if __name__ == "__main__":
    main()
