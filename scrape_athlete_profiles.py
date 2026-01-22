"""
Scrape detailed athlete profiles from TaekwondoData.com
Gets win/loss records, medal history, tournament participation
"""

import time
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

# Configure
BASE_URL = "https://www.taekwondodata.com"
OUTPUT_DIR = Path("data/athletes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def get_athlete_list_by_country(country_code: str = "KSA") -> list:
    """Get list of athletes from a specific country"""
    # TaekwondoData uses country pages like /saudi-arabia.a2rz.html
    country_urls = {
        'KSA': '/saudi-arabia.a2rz.html',
        'KOR': '/south-korea.afaw.html',
        'IRI': '/iran.a4g1.html',
        'JOR': '/jordan.a2jn.html',
        'TUR': '/turkey.a39v.html',
        'CHN': '/china.aean.html',
        'EGY': '/egypt.a2eu.html',
        'UAE': '/united-arab-emirates.a28o.html',
    }

    url = BASE_URL + country_urls.get(country_code, country_urls['KSA'])
    print(f"[FETCHING] {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        athletes = []
        # Find athlete links in the page
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Athlete pages have pattern like /name-name.xxxx.html
            if re.match(r'/[a-z-]+\.a[a-z0-9]+\.html', href):
                name = link.get_text(strip=True)
                if name and len(name) > 2:
                    athletes.append({
                        'name': name,
                        'url': BASE_URL + href,
                        'country': country_code
                    })

        print(f"[OK] Found {len(athletes)} athletes from {country_code}")
        return athletes

    except Exception as e:
        print(f"[ERROR] Failed to get athlete list: {e}")
        return []


def parse_athlete_profile(url: str) -> dict:
    """Parse detailed athlete profile from TaekwondoData.com"""
    print(f"  [FETCHING] {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        profile = {
            'url': url,
            'scraped_at': datetime.now().isoformat()
        }

        # Get page text for regex parsing
        page_text = soup.get_text()

        # Name - usually in h1 or title
        title = soup.find('title')
        if title:
            name_match = re.match(r'([^:]+)', title.get_text())
            if name_match:
                profile['name'] = name_match.group(1).strip()

        # Birth date
        birth_match = re.search(r'born\s+(\w+\s+\d+,\s+\d{4})', page_text, re.I)
        if birth_match:
            profile['birth_date'] = birth_match.group(1)

        # Fight record - "153 registered fights, fighter won 135 out of them. That's a rate of 88.2%"
        fight_match = re.search(r'(\d+)\s+registered\s+fights.*?won\s+(\d+).*?rate\s+of\s+([\d.]+)%', page_text, re.I)
        if fight_match:
            profile['total_fights'] = int(fight_match.group(1))
            profile['wins'] = int(fight_match.group(2))
            profile['win_rate'] = float(fight_match.group(3))
            profile['losses'] = profile['total_fights'] - profile['wins']

        # Points - "2,401 points distributed; 1,162 collected"
        points_match = re.search(r'([\d,]+)\s+points\s+distributed.*?([\d,]+)\s+collected', page_text, re.I)
        if points_match:
            profile['points_distributed'] = int(points_match.group(1).replace(',', ''))
            profile['points_collected'] = int(points_match.group(2).replace(',', ''))

        # Golden points - "Won 9 golden point(s) and lost 2"
        gp_match = re.search(r'Won\s+(\d+)\s+golden\s+point.*?lost\s+(\d+)', page_text, re.I)
        if gp_match:
            profile['golden_points_won'] = int(gp_match.group(1))
            profile['golden_points_lost'] = int(gp_match.group(2))

        # Tournaments - "Participated at 44 tournaments"
        tourney_match = re.search(r'Participated\s+at\s+(\d+)\s+tournaments', page_text, re.I)
        if tourney_match:
            profile['tournaments'] = int(tourney_match.group(1))

        # Weight categories competed in
        weight_match = re.search(r'competed\s+in\s+([-\d,\s+and]+)\s*kg', page_text, re.I)
        if weight_match:
            profile['weight_categories'] = weight_match.group(1).strip()

        # Current ranking - "Place 5 with 1,581 points"
        rank_match = re.search(r'Place\s+(\d+)\s+with\s+([\d,]+)\s+points', page_text, re.I)
        if rank_match:
            profile['current_rank'] = int(rank_match.group(1))
            profile['ranking_points'] = int(rank_match.group(2).replace(',', ''))

        # Medal counts - look for medal tables or text
        # Olympic medals
        olympic_match = re.search(r'Olympic\s+Games[:\s]*(\d+)\s*(?:gold|G).*?(\d+)\s*(?:silver|S).*?(\d+)\s*(?:bronze|B)', page_text, re.I)
        if olympic_match:
            profile['olympic_gold'] = int(olympic_match.group(1))
            profile['olympic_silver'] = int(olympic_match.group(2))
            profile['olympic_bronze'] = int(olympic_match.group(3))

        # World Championship medals
        worlds_match = re.search(r'World\s+Championships?[:\s]*(\d+)\s*(?:gold|G).*?(\d+)\s*(?:silver|S).*?(\d+)\s*(?:bronze|B)', page_text, re.I)
        if worlds_match:
            profile['world_gold'] = int(worlds_match.group(1))
            profile['world_silver'] = int(worlds_match.group(2))
            profile['world_bronze'] = int(worlds_match.group(3))

        # Count total medals from tables
        medal_tables = soup.find_all('table')
        total_gold = total_silver = total_bronze = 0
        for table in medal_tables:
            text = table.get_text()
            gold_cells = re.findall(r'(\d+)\s*(?:gold|G)', text, re.I)
            silver_cells = re.findall(r'(\d+)\s*(?:silver|S)', text, re.I)
            bronze_cells = re.findall(r'(\d+)\s*(?:bronze|B)', text, re.I)
            total_gold += sum(int(x) for x in gold_cells)
            total_silver += sum(int(x) for x in silver_cells)
            total_bronze += sum(int(x) for x in bronze_cells)

        if total_gold or total_silver or total_bronze:
            profile['total_gold'] = total_gold
            profile['total_silver'] = total_silver
            profile['total_bronze'] = total_bronze
            profile['total_medals'] = total_gold + total_silver + total_bronze

        return profile

    except Exception as e:
        print(f"  [ERROR] Failed to parse profile: {e}")
        return {'url': url, 'error': str(e)}


def scrape_ranked_athletes(rankings_df: pd.DataFrame) -> pd.DataFrame:
    """Scrape profiles for athletes in our rankings data"""

    profiles = []

    for idx, row in rankings_df.iterrows():
        athlete_name = row.get('athlete_name', '')
        country = row.get('country', '')

        # Clean name for URL search
        # Names are like "Mohamed Khalil JENDOUBI (TUN-1731)"
        name_match = re.match(r'([^(]+)', athlete_name)
        if name_match:
            clean_name = name_match.group(1).strip().lower()
            # Convert to URL format (spaces to hyphens)
            url_name = re.sub(r'\s+', '-', clean_name)
            url_name = re.sub(r'[^a-z-]', '', url_name)

            # Try to find on TaekwondoData
            search_url = f"{BASE_URL}/{url_name}.html"

            print(f"\n[{idx+1}/{len(rankings_df)}] Searching for {clean_name}...")

            # Note: This is a simplified approach - the actual URL structure varies
            # A more robust approach would use their search function

        time.sleep(1)  # Be nice to the server

    return pd.DataFrame(profiles)


def scrape_country_athletes(country_codes: list = None) -> pd.DataFrame:
    """Scrape all athletes from specified countries"""

    if country_codes is None:
        country_codes = ['KSA', 'JOR', 'UAE', 'EGY']  # Focus on regional rivals

    all_profiles = []

    for country in country_codes:
        print(f"\n{'='*60}")
        print(f"SCRAPING ATHLETES FROM {country}")
        print(f"{'='*60}")

        athletes = get_athlete_list_by_country(country)

        for i, athlete in enumerate(athletes):
            print(f"\n[{i+1}/{len(athletes)}] {athlete['name']}")
            profile = parse_athlete_profile(athlete['url'])
            profile['country_code'] = country
            all_profiles.append(profile)
            time.sleep(1.5)  # Be respectful

        print(f"\n[OK] Scraped {len(athletes)} profiles from {country}")

    return pd.DataFrame(all_profiles)


def main():
    """Main scraping function"""
    print("="*60)
    print("TAEKWONDO ATHLETE PROFILE SCRAPER")
    print("Source: TaekwondoData.com")
    print("="*60)

    # Option 1: Scrape Saudi and rival country athletes
    df = scrape_country_athletes(['KSA', 'JOR', 'UAE', 'EGY'])

    if not df.empty:
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d')
        output_file = OUTPUT_DIR / f'athlete_profiles_{timestamp}.csv'
        df.to_csv(output_file, index=False)
        print(f"\n[SAVED] {len(df)} profiles to {output_file}")

        # Also save as latest
        df.to_csv(OUTPUT_DIR / 'athlete_profiles_latest.csv', index=False)

        # Summary
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total profiles: {len(df)}")
        if 'total_fights' in df.columns:
            print(f"Athletes with fight records: {df['total_fights'].notna().sum()}")
        if 'win_rate' in df.columns:
            print(f"Average win rate: {df['win_rate'].mean():.1f}%")
        if 'total_medals' in df.columns:
            print(f"Total medals recorded: {df['total_medals'].sum():.0f}")
    else:
        print("\n[WARN] No profiles scraped")


if __name__ == '__main__':
    main()
