"""
Taekwondo PDF Data Extractor
Extracts competition data from PDFs with focus on:
- Competition names (World Junior Championships, Chuncheon 2024, etc.)
- Age brackets (Senior, Junior, U-21, Cadet, Children)
- Athlete names, countries, weight categories
- Results, draws, brackets
"""

import os
import re
import pdfplumber
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

class TaekwondoPDFExtractor:
    """Extract structured data from Taekwondo competition PDFs"""

    # Age bracket patterns
    AGE_BRACKETS = {
        'senior': r'\b(senior|adult)\b',
        'junior': r'\b(junior|jnr)\b',
        'u21': r'\b(u-?21|under.?21)\b',
        'cadet': r'\b(cadet|cdt)\b',
        'children': r'\b(children|child)\b',
        'youth': r'\b(youth)\b',
        'veteran': r'\b(veteran|vet)\b',
        'para': r'\b(para|paralympic)\b'
    }

    # Weight category patterns
    WEIGHT_PATTERNS = [
        r'(-?\d+)\s*kg',  # Matches: 54kg, 54 kg, -54kg
        r'(\d+)[-\+]',     # Matches: 54+, 54-
        r'under\s*(\d+)',  # Matches: under 54
        r'over\s*(\d+)'    # Matches: over 80
    ]

    # Competition type patterns
    COMPETITION_TYPES = [
        'World Championships',
        'Olympic Games',
        'Grand Prix',
        'Grand Slam',
        'Continental Championships',
        'Open Championships',
        'Poomsae Championships'
    ]

    def __init__(self, pdf_dir="downloaded_pdfs", output_dir="extracted_data"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.extracted_data = []

    def extract_competition_info(self, text, filename):
        """Extract competition name, location, year, age bracket from text"""
        info = {
            'source_file': filename,
            'competition_name': None,
            'location': None,
            'year': None,
            'age_bracket': None,
            'competition_type': None
        }

        # Extract year (2015-2026)
        year_match = re.search(r'20(1[5-9]|2[0-6])', text[:500])
        if year_match:
            info['year'] = int(year_match.group())

        # Extract age bracket
        text_lower = text.lower()
        for bracket, pattern in self.AGE_BRACKETS.items():
            if re.search(pattern, text_lower):
                info['age_bracket'] = bracket
                break

        # Also check filename for age bracket
        filename_lower = filename.lower()
        for bracket, pattern in self.AGE_BRACKETS.items():
            if re.search(pattern, filename_lower):
                info['age_bracket'] = bracket
                break

        # Extract competition type
        for comp_type in self.COMPETITION_TYPES:
            if comp_type.lower() in text_lower:
                info['competition_type'] = comp_type
                break

        # Extract location (capitalize words after common prefixes)
        location_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+20\d{2}',  # Location 2024
            r'20\d{2}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # 2024 Location
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text[:500])
            if match:
                info['location'] = match.group(1).strip()
                break

        # Try to extract from filename
        if not info['location']:
            # Pattern: Location_Year or Year_Location
            filename_parts = filename.replace('.pdf', '').split('_')
            for part in filename_parts:
                if part.istitle() and len(part) > 3 and not part.isdigit():
                    info['location'] = part
                    break

        # Build competition name
        parts = []
        if info['age_bracket']:
            parts.append(info['age_bracket'].title())
        if info['competition_type']:
            parts.append(info['competition_type'])
        if info['location']:
            parts.append(info['location'])
        if info['year']:
            parts.append(str(info['year']))

        if parts:
            info['competition_name'] = ' '.join(parts)
        else:
            # Use filename as fallback
            info['competition_name'] = filename.replace('.pdf', '').replace('_', ' ')

        return info

    def extract_tables(self, pdf_path):
        """Extract all tables from PDF"""
        tables_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get text from first 2 pages for metadata
                first_pages_text = ''
                for page in pdf.pages[:2]:
                    first_pages_text += page.extract_text() or ''

                # Extract competition info
                comp_info = self.extract_competition_info(first_pages_text, pdf_path.name)

                # Extract tables from all pages
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()

                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue

                        # Convert to DataFrame with unique column names
                        cols = table[0] if table[0] else [f"col_{i}" for i in range(len(table[0] if table else []))]

                        # Make columns unique
                        seen = {}
                        unique_cols = []
                        for col in cols:
                            if col in seen:
                                seen[col] += 1
                                unique_cols.append(f"{col}_{seen[col]}")
                            else:
                                seen[col] = 0
                                unique_cols.append(col)

                        df = pd.DataFrame(table[1:], columns=unique_cols)

                        # Clean up DataFrame
                        df = df.dropna(how='all')  # Remove empty rows
                        df = df.loc[:, df.columns.notna()]  # Remove unnamed columns

                        if len(df) > 0:
                            # Add metadata columns
                            for key, value in comp_info.items():
                                df[key] = value

                            df['page_number'] = page_num
                            df['table_index'] = table_idx

                            tables_data.append(df)

            return tables_data, comp_info

        except Exception as e:
            print(f"  [ERROR] {pdf_path.name}: {e}")
            return [], None

    def extract_weight_category(self, text):
        """Extract weight category from text"""
        if not text or not isinstance(text, str):
            return None

        for pattern in self.WEIGHT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def find_athlete_columns(self, df):
        """Identify columns containing athlete data"""
        athlete_cols = {
            'name': None,
            'country': None,
            'weight': None,
            'result': None
        }

        for col in df.columns:
            col_lower = str(col).lower() if col else ''

            # Name column
            if any(keyword in col_lower for keyword in ['name', 'athlete', 'player', 'fighter']):
                athlete_cols['name'] = col

            # Country column
            elif any(keyword in col_lower for keyword in ['country', 'nation', 'noc', 'team']):
                athlete_cols['country'] = col

            # Weight column
            elif any(keyword in col_lower for keyword in ['weight', 'category', 'division']):
                athlete_cols['weight'] = col

            # Result column
            elif any(keyword in col_lower for keyword in ['result', 'place', 'rank', 'position', 'medal']):
                athlete_cols['result'] = col

        return athlete_cols

    def process_category(self, category_path):
        """Process all PDFs in a category folder"""
        print(f"\n[{category_path.name.upper()}]")
        print("=" * 70)

        pdf_files = list(category_path.glob("*.pdf"))
        if not pdf_files:
            print("  No PDF files found")
            return

        print(f"  Found {len(pdf_files)} PDF files")

        category_output = self.output_dir / category_path.name
        category_output.mkdir(exist_ok=True)

        all_data = []

        for pdf_file in pdf_files:
            print(f"\n  Processing: {pdf_file.name}")

            tables, comp_info = self.extract_tables(pdf_file)

            if not tables:
                print(f"    No tables extracted")
                continue

            print(f"    Extracted {len(tables)} tables")

            # Save each table
            for idx, df in enumerate(tables):
                # Identify athlete columns
                athlete_cols = self.find_athlete_columns(df)

                # Extract weight categories from appropriate column
                if athlete_cols['weight']:
                    df['weight_category'] = df[athlete_cols['weight']].apply(self.extract_weight_category)

                all_data.append(df)

                # Save individual table
                table_filename = f"{pdf_file.stem}_table{idx}.csv"
                table_path = category_output / table_filename
                df.to_csv(table_path, index=False, encoding='utf-8')
                print(f"      Saved: {table_filename} ({len(df)} rows)")

        # Combine all tables for this category
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_path = category_output / f"{category_path.name}_combined.csv"
            combined_df.to_csv(combined_path, index=False, encoding='utf-8')
            print(f"\n  [COMBINED] {combined_path.name} ({len(combined_df)} total rows)")

            self.extracted_data.append({
                'category': category_path.name,
                'files_processed': len(pdf_files),
                'tables_extracted': len(all_data),
                'total_rows': len(combined_df),
                'output_file': str(combined_path)
            })

    def extract_all(self):
        """Extract data from all PDF categories"""
        print("=" * 70)
        print("TAEKWONDO PDF DATA EXTRACTOR")
        print("Extracting: Competition Names | Age Brackets | Athletes | Results")
        print("=" * 70)

        # Get all category folders
        category_folders = [d for d in self.pdf_dir.iterdir() if d.is_dir()]

        if not category_folders:
            print(f"\n[ERROR] No category folders found in {self.pdf_dir}")
            return

        print(f"\nFound {len(category_folders)} categories to process")

        # Process each category
        for category_path in sorted(category_folders):
            self.process_category(category_path)

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate extraction summary"""
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)

        if not self.extracted_data:
            print("\nNo data extracted")
            return

        total_files = sum(item['files_processed'] for item in self.extracted_data)
        total_tables = sum(item['tables_extracted'] for item in self.extracted_data)
        total_rows = sum(item['total_rows'] for item in self.extracted_data)

        print(f"\n[TOTAL]")
        print(f"  Categories: {len(self.extracted_data)}")
        print(f"  PDF files: {total_files}")
        print(f"  Tables extracted: {total_tables}")
        print(f"  Total rows: {total_rows}")

        print(f"\n[BY CATEGORY]")
        for item in self.extracted_data:
            print(f"  {item['category']}: {item['total_rows']} rows from {item['files_processed']} PDFs")

        print(f"\n[OUTPUT] {self.output_dir.absolute()}")

        # Save summary
        summary_path = self.output_dir / f"extraction_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'categories': len(self.extracted_data),
                    'total_files': total_files,
                    'total_tables': total_tables,
                    'total_rows': total_rows
                },
                'details': self.extracted_data
            }, f, indent=2)

        print(f"\n[SAVED] {summary_path}")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract structured data from Taekwondo PDFs')
    parser.add_argument('--input', default='downloaded_pdfs', help='Input directory with PDF folders')
    parser.add_argument('--output', default='extracted_data', help='Output directory for CSV files')

    args = parser.parse_args()

    try:
        extractor = TaekwondoPDFExtractor(pdf_dir=args.input, output_dir=args.output)
        extractor.extract_all()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
