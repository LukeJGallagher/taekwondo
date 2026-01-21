"""Quick test to check if we can access World Taekwondo data"""

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("Testing World Taekwondo data access...")
print("=" * 70)

# Test 1: Check main website
print("\n[1] Main website:")
try:
    response = session.get("https://www.worldtaekwondo.org", verify=False, timeout=10)
    print(f"  Status: {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Check rankings page
print("\n[2] Rankings page:")
try:
    response = session.get("https://www.worldtaekwondo.org/athletes/Ranking/contents", verify=False, timeout=10)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for download links
        links = soup.find_all('a', href=True)
        download_links = []

        for link in links:
            href = link['href']
            if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                download_links.append({
                    'text': link.get_text(strip=True),
                    'href': href
                })

        if download_links:
            print(f"  Found {len(download_links)} downloadable files:")
            for dl in download_links[:5]:  # Show first 5
                print(f"    - {dl['text'][:50]}: {dl['href'][:80]}")
        else:
            print("  No direct download links found")

        # Look for iframes
        iframes = soup.find_all('iframe')
        if iframes:
            print(f"\n  Found {len(iframes)} iframes:")
            for iframe in iframes:
                src = iframe.get('src', '')
                print(f"    - {src[:100]}")

except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Check specific file patterns
print("\n[3] Testing specific file URLs:")
test_urls = [
    "https://www.worldtaekwondo.org/att_file_up/athletes/2025/World_Ranking_May_2025.xlsx",
    "https://www.worldtaekwondo.org/att_file_up/athletes/2024/World_Ranking_December_2024.xlsx",
    "https://www.worldtaekwondo.org/wp-content/uploads/2024/results.pdf",
]

for url in test_urls:
    try:
        response = session.head(url, verify=False, timeout=5)
        print(f"  {response.status_code}: {url}")
    except Exception as e:
        print(f"  ERROR: {url}")

# Test 4: SimplyCompete with proper headers
print("\n[4] Testing SimplyCompete API:")
simplycompete_session = requests.Session()
simplycompete_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.worldtaekwondo.org/athletes/Ranking/contents',
    'Origin': 'https://www.worldtaekwondo.org',
})

test_api_urls = [
    "https://worldtkd.simplycompete.com/playerRankingV2",
    "https://worldtkd.simplycompete.com/events",
]

for url in test_api_urls:
    try:
        response = simplycompete_session.get(url, verify=False, timeout=10)
        print(f"  {response.status_code}: {url}")
        if response.status_code == 200:
            print(f"    Content-Type: {response.headers.get('content-type')}")
            print(f"    Response size: {len(response.text)} bytes")
    except Exception as e:
        print(f"  ERROR: {url} - {e}")

print("\n" + "=" * 70)
print("Test complete!")
