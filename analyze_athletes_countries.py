"""
Analyze Athletes and Countries from Extracted Taekwondo Data
Creates comprehensive reports on athletes and countries across all competitions
"""

import pandas as pd
from pathlib import Path
import json
from collections import Counter
from datetime import datetime

class AthleteCountryAnalyzer:
    def __init__(self, extracted_dir="extracted_data"):
        self.extracted_dir = Path(extracted_dir)
        self.all_data = []
        self.athletes = []
        self.countries = []

    def load_all_data(self):
        """Load all combined CSV files from extracted_data"""
        print("="*70)
        print("LOADING EXTRACTED DATA")
        print("="*70)

        combined_files = list(self.extracted_dir.rglob("*_combined.csv"))
        print(f"\nFound {len(combined_files)} combined CSV files")

        for csv_file in combined_files:
            try:
                df = pd.read_csv(csv_file)
                category = csv_file.parent.name
                df['category'] = category
                self.all_data.append(df)
                print(f"  Loaded: {csv_file.name} ({len(df)} rows)")
            except Exception as e:
                print(f"  [ERROR] {csv_file.name}: {e}")

        if self.all_data:
            self.combined_df = pd.concat(self.all_data, ignore_index=True)
            print(f"\n[TOTAL] {len(self.combined_df)} rows across all categories")
        else:
            print("\n[ERROR] No data loaded!")
            self.combined_df = pd.DataFrame()

    def extract_athletes(self):
        """Extract athlete names from the data"""
        print(f"\n{'='*70}")
        print("EXTRACTING ATHLETE INFORMATION")
        print(f"{'='*70}")

        if self.combined_df.empty:
            print("No data to analyze")
            return

        # Look for columns that might contain athlete names
        name_columns = [col for col in self.combined_df.columns if any(
            keyword in col.lower() for keyword in ['name', 'athlete', 'player', 'fighter'])]

        print(f"\nFound {len(name_columns)} potential name columns: {name_columns}")

        athletes_data = []

        for col in name_columns:
            # Get all non-null values
            values = self.combined_df[col].dropna().unique()
            print(f"\n  {col}: {len(values)} unique values")

            for value in values:
                if isinstance(value, str) and len(value) > 2:
                    # Get rows with this athlete
                    athlete_rows = self.combined_df[self.combined_df[col] == value]

                    athlete_info = {
                        'name': value,
                        'column_found': col,
                        'appearances': len(athlete_rows),
                        'categories': athlete_rows['category'].unique().tolist() if 'category' in athlete_rows.columns else [],
                        'competitions': athlete_rows['competition_name'].unique().tolist() if 'competition_name' in athlete_rows.columns else [],
                        'years': athlete_rows['year'].unique().tolist() if 'year' in athlete_rows.columns else []
                    }

                    athletes_data.append(athlete_info)

        self.athletes = athletes_data
        print(f"\n[EXTRACTED] {len(self.athletes)} total athlete entries")

    def extract_countries(self):
        """Extract country information from the data"""
        print(f"\n{'='*70}")
        print("EXTRACTING COUNTRY INFORMATION")
        print(f"{'='*70}")

        if self.combined_df.empty:
            print("No data to analyze")
            return

        # Look for columns that might contain country codes/names
        country_columns = [col for col in self.combined_df.columns if any(
            keyword in col.lower() for keyword in ['country', 'nation', 'noc', 'team'])]

        print(f"\nFound {len(country_columns)} potential country columns: {country_columns}")

        countries_data = []

        for col in country_columns:
            # Get all non-null values
            values = self.combined_df[col].dropna().unique()
            print(f"\n  {col}: {len(values)} unique values")

            for value in values:
                if isinstance(value, str) and len(value) > 0:
                    # Get rows with this country
                    country_rows = self.combined_df[self.combined_df[col] == value]

                    country_info = {
                        'country': value,
                        'column_found': col,
                        'appearances': len(country_rows),
                        'categories': country_rows['category'].unique().tolist() if 'category' in country_rows.columns else [],
                        'competitions': country_rows['competition_name'].unique().tolist() if 'competition_name' in country_rows.columns else [],
                        'years': country_rows['year'].unique().tolist() if 'year' in country_rows.columns else []
                    }

                    countries_data.append(country_info)

        self.countries = countries_data
        print(f"\n[EXTRACTED] {len(self.countries)} total country entries")

    def create_summaries(self):
        """Create summary reports"""
        print(f"\n{'='*70}")
        print("CREATING SUMMARY REPORTS")
        print(f"{'='*70}")

        summaries = {}

        # Category breakdown
        if 'category' in self.combined_df.columns:
            category_counts = self.combined_df['category'].value_counts()
            summaries['by_category'] = category_counts.to_dict()
            print("\n[BY CATEGORY]")
            for cat, count in category_counts.items():
                print(f"  {cat}: {count} rows")

        # Competition breakdown
        if 'competition_name' in self.combined_df.columns:
            comp_counts = self.combined_df['competition_name'].value_counts()
            summaries['by_competition'] = comp_counts.head(20).to_dict()
            print("\n[TOP 20 COMPETITIONS]")
            for comp, count in comp_counts.head(20).items():
                print(f"  {comp}: {count} rows")

        # Year breakdown
        if 'year' in self.combined_df.columns:
            year_counts = self.combined_df['year'].value_counts().sort_index()
            summaries['by_year'] = {int(k): int(v) for k, v in year_counts.items() if pd.notna(k)}
            print("\n[BY YEAR]")
            for year, count in year_counts.items():
                if pd.notna(year):
                    print(f"  {int(year)}: {count} rows")

        # Age bracket breakdown
        if 'age_bracket' in self.combined_df.columns:
            age_counts = self.combined_df['age_bracket'].value_counts()
            summaries['by_age_bracket'] = age_counts.to_dict()
            print("\n[BY AGE BRACKET]")
            for bracket, count in age_counts.items():
                if pd.notna(bracket):
                    print(f"  {bracket}: {count} rows")

        return summaries

    def save_reports(self):
        """Save all reports to files"""
        output_dir = Path("analysis_reports")
        output_dir.mkdir(exist_ok=True)

        print(f"\n{'='*70}")
        print(f"SAVING REPORTS TO: {output_dir.absolute()}")
        print(f"{'='*70}")

        # Save athletes
        if self.athletes:
            athletes_file = output_dir / "athletes_list.json"
            with open(athletes_file, 'w', encoding='utf-8') as f:
                json.dump(self.athletes, f, indent=2)
            print(f"\n[SAVED] {len(self.athletes)} athletes -> {athletes_file.name}")

            # Create athletes CSV
            try:
                athletes_df = pd.DataFrame(self.athletes)
                athletes_df['categories'] = athletes_df['categories'].apply(lambda x: ', '.join(x) if x else '')
                athletes_df['competitions'] = athletes_df['competitions'].apply(lambda x: ', '.join(str(c) for c in x[:3]) if x else '')
                athletes_csv = output_dir / "athletes_list.csv"
                athletes_df.to_csv(athletes_csv, index=False, encoding='utf-8')
                print(f"[SAVED] Athletes CSV -> {athletes_csv.name}")
            except Exception as e:
                print(f"[ERROR] Could not create athletes CSV: {e}")

        # Save countries
        if self.countries:
            countries_file = output_dir / "countries_list.json"
            with open(countries_file, 'w', encoding='utf-8') as f:
                json.dump(self.countries, f, indent=2)
            print(f"\n[SAVED] {len(self.countries)} countries -> {countries_file.name}")

            # Create countries CSV
            try:
                countries_df = pd.DataFrame(self.countries)
                countries_df['categories'] = countries_df['categories'].apply(lambda x: ', '.join(x) if x else '')
                countries_df['competitions'] = countries_df['competitions'].apply(lambda x: ', '.join(str(c) for c in x[:3]) if x else '')
                countries_csv = output_dir / "countries_list.csv"
                countries_df.to_csv(countries_csv, index=False, encoding='utf-8')
                print(f"[SAVED] Countries CSV -> {countries_csv.name}")
            except Exception as e:
                print(f"[ERROR] Could not create countries CSV: {e}")

        # Save summaries
        summaries = self.create_summaries()
        summary_file = output_dir / "data_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_rows': len(self.combined_df),
                'total_athletes': len(self.athletes),
                'total_countries': len(self.countries),
                'summaries': summaries
            }, f, indent=2)
        print(f"\n[SAVED] Summary -> {summary_file.name}")

        print(f"\n{'='*70}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*70}")

def main():
    analyzer = AthleteCountryAnalyzer()

    try:
        analyzer.load_all_data()
        analyzer.extract_athletes()
        analyzer.extract_countries()
        analyzer.save_reports()

        print(f"\n[SUCCESS] Check 'analysis_reports' folder for results")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
