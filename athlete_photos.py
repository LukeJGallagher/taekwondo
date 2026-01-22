"""
Athlete Photo Management System
================================
Simple URL-based photo linking for athletes - no file storage needed.
Just stores photo URLs and generates HTML for dashboard display.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Photo index storage
PHOTOS_DIR = Path("data/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
PHOTO_INDEX_FILE = PHOTOS_DIR / "photo_urls.json"


class AthletePhotoManager:
    """Simple URL-based photo management - no file downloads"""

    def __init__(self):
        self.photo_urls: Dict[str, Dict] = {}
        self.load_index()

    def load_index(self):
        """Load photo URL index from JSON"""
        if PHOTO_INDEX_FILE.exists():
            with open(PHOTO_INDEX_FILE, 'r', encoding='utf-8') as f:
                self.photo_urls = json.load(f)

    def save_index(self):
        """Save photo URL index to JSON"""
        with open(PHOTO_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.photo_urls, f, indent=2, ensure_ascii=False)

    def add_photo_url(self, athlete_name: str, photo_url: str,
                      weight_category: str = "",
                      country: str = "",
                      simplycompete_id: str = "") -> bool:
        """Add or update photo URL for an athlete"""
        self.photo_urls[athlete_name] = {
            'url': photo_url,
            'weight_category': weight_category,
            'country': country,
            'simplycompete_id': simplycompete_id,
            'added_at': datetime.now().isoformat()
        }
        self.save_index()
        print(f"[OK] Added photo URL for {athlete_name}")
        return True

    def get_photo_url(self, athlete_name: str) -> Optional[str]:
        """Get photo URL for an athlete"""
        if athlete_name in self.photo_urls:
            return self.photo_urls[athlete_name].get('url')
        return None

    def get_photo_html(self, athlete_name: str, size: int = 100, rounded: bool = True) -> str:
        """
        Get HTML for athlete photo.
        Uses URL if available, otherwise shows placeholder with initials.
        """
        url = self.get_photo_url(athlete_name)
        border_radius = '50%' if rounded else '8px'

        if url:
            return f'''
            <img src="{url}"
                 style="width: {size}px; height: {size}px; object-fit: cover; border-radius: {border_radius};
                        border: 3px solid #1E5631; box-shadow: 0 4px 8px rgba(0,0,0,0.2);"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div style="width: {size}px; height: {size}px; background: linear-gradient(135deg, #1E5631 0%, #163d24 100%);
                 border-radius: {border_radius}; display: none; align-items: center; justify-content: center;
                 color: white; font-size: {size//3}px; font-weight: bold; border: 3px solid #a08e66;">
                {self._get_initials(athlete_name)}
            </div>
            '''

        # No URL - show placeholder with initials
        initials = self._get_initials(athlete_name)
        return f'''
        <div style="width: {size}px; height: {size}px; background: linear-gradient(135deg, #1E5631 0%, #163d24 100%);
             border-radius: {border_radius}; display: flex; align-items: center; justify-content: center;
             color: white; font-size: {size//3}px; font-weight: bold; border: 3px solid #a08e66;
             box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            {initials}
        </div>
        '''

    def _get_initials(self, name: str) -> str:
        """Get initials from name"""
        words = name.split()
        if len(words) >= 2:
            return (words[0][0] + words[-1][0]).upper()
        return name[:2].upper()

    def remove_photo(self, athlete_name: str) -> bool:
        """Remove photo URL for an athlete"""
        if athlete_name in self.photo_urls:
            del self.photo_urls[athlete_name]
            self.save_index()
            return True
        return False

    def list_all(self) -> List[Dict]:
        """List all athletes with photos"""
        return [
            {'name': name, 'url': info.get('url'), 'category': info.get('weight_category')}
            for name, info in self.photo_urls.items()
        ]

    def bulk_add(self, athletes: List[Dict]):
        """
        Bulk add photo URLs.
        Each dict should have: name, url, category (optional), country (optional)
        """
        for athlete in athletes:
            self.add_photo_url(
                athlete_name=athlete['name'],
                photo_url=athlete['url'],
                weight_category=athlete.get('category', ''),
                country=athlete.get('country', '')
            )


def create_athlete_card_html(athlete_name: str,
                             weight_category: str,
                             rank: Optional[int] = None,
                             points: Optional[float] = None,
                             country: str = "",
                             photo_manager: Optional[AthletePhotoManager] = None) -> str:
    """Generate HTML athlete card with photo for dashboard"""

    if photo_manager is None:
        photo_manager = AthletePhotoManager()

    photo_html = photo_manager.get_photo_html(athlete_name, size=80, rounded=True)

    rank_display = f"#{rank}" if rank else "Unranked"
    points_display = f"{points:.1f} pts" if points else "-"
    country_display = f" ({country})" if country else ""

    return f'''
    <div style="background: white; border-radius: 12px; padding: 1rem;
         box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid #1E5631;
         display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
        {photo_html}
        <div style="flex: 1;">
            <h4 style="margin: 0; color: #333; font-size: 1rem;">{athlete_name}</h4>
            <p style="margin: 0.25rem 0 0 0; color: #666; font-size: 0.85rem;">{weight_category}{country_display}</p>
            <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                <span style="background: #1E5631; color: white; padding: 0.2rem 0.5rem;
                       border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{rank_display}</span>
                <span style="background: #a08e66; color: white; padding: 0.2rem 0.5rem;
                       border-radius: 4px; font-size: 0.75rem;">{points_display}</span>
            </div>
        </div>
    </div>
    '''


def create_athlete_row_html(athlete_name: str,
                            weight_category: str,
                            rank: int,
                            points: float,
                            country: str = "",
                            photo_manager: Optional[AthletePhotoManager] = None) -> str:
    """Generate compact HTML row for athlete lists"""

    if photo_manager is None:
        photo_manager = AthletePhotoManager()

    photo_html = photo_manager.get_photo_html(athlete_name, size=40, rounded=True)

    return f'''
    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem;
         border-bottom: 1px solid #eee;">
        {photo_html}
        <span style="width: 40px; font-weight: bold; color: #1E5631;">#{rank}</span>
        <span style="flex: 1; font-weight: 500;">{athlete_name}</span>
        <span style="width: 80px; color: #666;">{weight_category}</span>
        <span style="width: 80px; color: #666;">{country}</span>
        <span style="width: 60px; text-align: right; font-weight: 500;">{points:.1f}</span>
    </div>
    '''


# SimplyCompete profile photo URL pattern (if available)
def get_simplycompete_profile_url(athlete_id: str) -> str:
    """
    Generate SimplyCompete profile page URL.
    Photos can be manually copied from these pages.
    """
    return f"https://worldtkd.simplycompete.com/playerProfileV2?userId={athlete_id}"


def main():
    """Demo the URL-based photo system"""
    print("="*60)
    print("ATHLETE PHOTO URL SYSTEM")
    print("="*60)

    manager = AthletePhotoManager()

    # Example: Add some photo URLs
    print("\nExample usage:")
    print("-" * 40)

    example_code = '''
# Add photo URL for athlete
manager = AthletePhotoManager()

manager.add_photo_url(
    athlete_name="Mohamed Khalil JENDOUBI",
    photo_url="https://example.com/jendoubi.jpg",
    weight_category="M-54kg",
    country="Tunisia"
)

# Get HTML for dashboard (returns placeholder if no URL)
html = manager.get_photo_html("Mohamed Khalil JENDOUBI", size=100)

# Create full athlete card
from athlete_photos import create_athlete_card_html
card = create_athlete_card_html(
    athlete_name="Mohamed Khalil JENDOUBI",
    weight_category="M-54kg",
    rank=1,
    points=230.4,
    country="Tunisia"
)

# Bulk add from scraped data
athletes_with_photos = [
    {"name": "Athlete 1", "url": "https://...", "category": "M-68kg"},
    {"name": "Athlete 2", "url": "https://...", "category": "F-57kg"},
]
manager.bulk_add(athletes_with_photos)
'''
    print(example_code)

    # Show current index
    all_photos = manager.list_all()
    print(f"\nCurrently indexed: {len(all_photos)} athletes")

    return manager


if __name__ == '__main__':
    main()
