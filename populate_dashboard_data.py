"""
Populate Dashboard Data
Extracts athlete and match data from available sources to populate the dashboard
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from pathlib import Path
from datetime import datetime

def extract_athletes_from_rankings():
    """Extract athlete data from rankings"""
    print("Extracting athletes from rankings...")

    # Load rankings
    rankings_file = Path("data/rankings/world_rankings_latest.csv")
    if not rankings_file.exists():
        print("  No rankings file found")
        return None

    df = pd.read_csv(rankings_file, encoding='utf-8-sig')
    print(f"  Loaded {len(df)} athletes from rankings")

    # Extract athlete information
    athletes = []
    for _, row in df.iterrows():
        # Parse name and ID from format: "NAME (COUNTRY-ID)"
        name_full = row['NAME']

        # Try to extract ID from name
        athlete_id = None
        if '(' in name_full and ')' in name_full:
            parts = name_full.split('(')
            name = parts[0].strip()
            id_part = parts[1].replace(')', '')
            if '-' in id_part:
                athlete_id = id_part.split('-')[1]
        else:
            name = name_full

        athlete = {
            'id': athlete_id or f"ATH_{row['RANK']}",
            'name': name,
            'country': row['MEMBER NATION'],
            'rank': row['RANK'],
            'points': row['POINTS'],
            'rank_change': row['↑↓'] if '↑↓' in df.columns else 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        athletes.append(athlete)

    athletes_df = pd.DataFrame(athletes)

    # Save to data/athletes
    output_file = Path("data/athletes/athletes_from_rankings.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    athletes_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"  ✓ Saved {len(athletes_df)} athletes to {output_file}")
    return athletes_df

def extract_matches_from_competitions():
    """Extract match data from competition files"""
    print("\nExtracting matches from competitions...")

    # Find competition result files
    comp_files = list(Path("data/competitions").glob("*results*.csv"))

    if not comp_files:
        print("  No competition result files found")
        return None

    all_matches = []

    for comp_file in comp_files:
        try:
            df = pd.read_csv(comp_file, encoding='utf-8-sig')

            if df.empty:
                continue

            # Add competition info
            df['competition'] = comp_file.stem
            df['source_file'] = comp_file.name

            all_matches.append(df)
            print(f"  Loaded {len(df)} matches from {comp_file.name}")

        except Exception as e:
            print(f"  Error loading {comp_file.name}: {e}")
            continue

    if not all_matches:
        print("  No valid match data found")
        return None

    # Combine all matches
    matches_df = pd.concat(all_matches, ignore_index=True)

    # Save to data/matches
    output_file = Path("data/matches/all_matches.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    matches_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"  ✓ Saved {len(matches_df)} total matches to {output_file}")
    return matches_df

def create_saudi_athlete_summary():
    """Create summary of Saudi athletes"""
    print("\nCreating Saudi athlete summary...")

    # Load athletes
    athletes_file = Path("data/athletes/athletes_from_rankings.csv")
    if not athletes_file.exists():
        print("  No athlete data available")
        return None

    df = pd.read_csv(athletes_file)

    # Filter Saudi athletes
    saudi_df = df[df['country'].str.contains('Saudi|KSA', case=False, na=False)]

    if len(saudi_df) == 0:
        print("  No Saudi athletes found in rankings")
        # Create placeholder
        saudi_df = pd.DataFrame([{
            'id': 'KSA_001',
            'name': 'No Saudi Athletes Currently Ranked',
            'country': 'Saudi Arabia',
            'rank': 0,
            'points': 0,
            'rank_change': 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }])

    # Save Saudi-specific file
    output_file = Path("data/athletes/saudi_athletes.csv")
    saudi_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"  ✓ Saved {len(saudi_df)} Saudi athletes to {output_file}")
    return saudi_df

def populate_all_data():
    """Main function to populate all dashboard data"""
    print("="*70)
    print("POPULATING DASHBOARD DATA")
    print("="*70)

    # Extract athletes from rankings
    athletes_df = extract_athletes_from_rankings()

    # Extract matches from competitions
    matches_df = extract_matches_from_competitions()

    # Create Saudi athlete summary
    saudi_df = create_saudi_athlete_summary()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    if athletes_df is not None:
        print(f"✓ Athletes: {len(athletes_df)} total")
        if saudi_df is not None:
            print(f"  - Saudi athletes: {len(saudi_df)}")

    if matches_df is not None:
        print(f"✓ Matches: {len(matches_df)} total")

        # Count by competition
        if 'competition' in matches_df.columns:
            comp_counts = matches_df['competition'].value_counts()
            print(f"  - Competitions: {len(comp_counts)}")
            for comp, count in comp_counts.head(5).items():
                print(f"    • {comp}: {count} matches")

    print("\n✓ Dashboard data populated successfully!")
    print("  Restart the dashboard or refresh your browser")
    print("="*70)

if __name__ == "__main__":
    populate_all_data()
