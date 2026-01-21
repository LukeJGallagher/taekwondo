"""
Download all PDF files cataloged from World Taekwondo scraping
Reads all downloadable_files.json and downloads the PDFs
"""

import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import time
from datetime import datetime

class PDFDownloader:
    """Download all PDFs found during scraping"""

    def __init__(self, base_dir="data_all_categories", output_dir="downloaded_pdfs"):
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.downloaded = []
        self.failed = []
        self.skipped = []

    def sanitize_filename(self, url):
        """Create a safe filename from URL"""
        # Get filename from URL
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path))

        # Clean up
        filename = filename.replace('%20', '_')
        filename = filename.replace(' ', '_')

        # Ensure it has an extension
        if not filename.lower().endswith(('.pdf', '.xlsx', '.xls', '.csv')):
            filename += '.pdf'

        return filename

    def download_file(self, url, category):
        """Download a single file"""
        try:
            # Create category subfolder
            category_dir = self.output_dir / category
            category_dir.mkdir(exist_ok=True)

            # Get filename
            filename = self.sanitize_filename(url)
            filepath = category_dir / filename

            # Skip if already downloaded
            if filepath.exists():
                print(f"  [SKIP] Already exists: {filename}")
                self.skipped.append({'url': url, 'file': str(filepath)})
                return True

            # Download
            print(f"  [DOWNLOAD] {filename}")
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()

            # Save
            with open(filepath, 'wb') as f:
                f.write(response.content)

            file_size = filepath.stat().st_size / 1024  # KB
            print(f"  [SAVED] {filename} ({file_size:.1f} KB)")

            self.downloaded.append({
                'url': url,
                'file': str(filepath),
                'size': file_size,
                'category': category
            })

            return True

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to download {url}: {e}")
            self.failed.append({'url': url, 'error': str(e)})
            return False
        except Exception as e:
            print(f"  [ERROR] Unexpected error for {url}: {e}")
            self.failed.append({'url': url, 'error': str(e)})
            return False

    def find_json_files(self):
        """Find all downloadable_files.json files"""
        json_files = []

        # Search all subdirectories
        for json_file in self.base_dir.rglob("downloadable_files.json"):
            # Get category name from parent directory
            category = json_file.parent.name
            json_files.append((category, json_file))

        return json_files

    def download_all(self):
        """Download all PDFs from all categories"""
        print("=" * 70)
        print("PDF DOWNLOADER - World Taekwondo Data")
        print("=" * 70)

        # Find all JSON files
        json_files = self.find_json_files()
        print(f"\nFound {len(json_files)} categories with downloadable files\n")

        if not json_files:
            print("[ERROR] No downloadable_files.json found!")
            print(f"Looking in: {self.base_dir.absolute()}")
            return

        # Process each category
        for category, json_file in json_files:
            print(f"\n[{category.upper()}]")
            print("-" * 70)

            try:
                # Read JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    files_data = json.load(f)

                if not files_data:
                    print("  No files to download")
                    continue

                print(f"  Found {len(files_data)} files")

                # Download each file
                for file_info in files_data:
                    url = file_info.get('url', '')
                    if url:
                        self.download_file(url, category)
                        time.sleep(0.5)  # Be nice to the server

            except json.JSONDecodeError as e:
                print(f"  [ERROR] Invalid JSON: {e}")
            except Exception as e:
                print(f"  [ERROR] {e}")

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print download summary"""
        print("\n" + "=" * 70)
        print("DOWNLOAD SUMMARY")
        print("=" * 70)

        print(f"\n[DOWNLOADED] {len(self.downloaded)} files")
        if self.downloaded:
            total_size = sum(f['size'] for f in self.downloaded)
            print(f"  Total size: {total_size:.1f} KB ({total_size/1024:.1f} MB)")

            # Group by category
            categories = {}
            for item in self.downloaded:
                cat = item['category']
                categories[cat] = categories.get(cat, 0) + 1

            print("\n  By category:")
            for cat, count in sorted(categories.items()):
                print(f"    {cat}: {count} files")

        print(f"\n[SKIPPED] {len(self.skipped)} files (already downloaded)")

        print(f"\n[FAILED] {len(self.failed)} files")
        if self.failed:
            print("  Failed downloads:")
            for item in self.failed[:10]:  # Show first 10
                print(f"    - {item['url']}")
                print(f"      Error: {item['error']}")

        print(f"\n[OUTPUT] Downloaded files in: {self.output_dir.absolute()}")

        # Save summary
        summary_file = self.output_dir / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'downloaded': self.downloaded,
                'skipped': self.skipped,
                'failed': self.failed,
                'stats': {
                    'total_downloaded': len(self.downloaded),
                    'total_skipped': len(self.skipped),
                    'total_failed': len(self.failed)
                }
            }, f, indent=2)

        print(f"\n[SAVED] Summary: {summary_file}")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download all PDFs from scraped data')
    parser.add_argument('--input', default='data_all_categories', help='Input directory with JSON files')
    parser.add_argument('--output', default='downloaded_pdfs', help='Output directory for PDFs')

    args = parser.parse_args()

    try:
        downloader = PDFDownloader(base_dir=args.input, output_dir=args.output)
        downloader.download_all()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
