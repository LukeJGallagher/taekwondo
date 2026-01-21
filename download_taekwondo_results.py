"""
World Taekwondo Result Book Downloader
Downloads all result books from the World Taekwondo RECORD&STATS page
"""

import os
import re
import time
import urllib3
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Disable SSL warnings (use with caution)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaekwondoDownloader:
    def __init__(self, base_url, download_dir="result_books"):
        """
        Initialize the downloader

        Args:
            base_url: The URL of the page containing result books
            download_dir: Directory to save downloaded files
        """
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

        # Set up session with headers to mimic browser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_page_content(self):
        """Fetch the page content"""
        try:
            print(f"Fetching page: {self.base_url}")
            response = self.session.get(self.base_url, verify=False, timeout=30)
            response.raise_for_status()
            print(f"[OK] Page fetched successfully (Status: {response.status_code})")
            return response.text
        except Exception as e:
            print(f"[ERROR] Error fetching page: {e}")
            return None

    def extract_download_links(self, html_content):
        """
        Extract all download links from the page

        Args:
            html_content: HTML content of the page

        Returns:
            List of tuples (url, filename)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        download_links = []

        # Look for PDF links
        pdf_extensions = ['.pdf', '.PDF']
        doc_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.zip']
        all_extensions = pdf_extensions + doc_extensions

        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Check if it's a downloadable file
            if any(ext in href for ext in all_extensions):
                # Make absolute URL
                absolute_url = urljoin(self.base_url, href)

                # Try to get a descriptive filename
                link_text = link.get_text(strip=True)

                # Extract filename from URL
                parsed_url = urlparse(absolute_url)
                url_filename = os.path.basename(parsed_url.path)

                # Use link text as filename if available, otherwise use URL filename
                if link_text and len(link_text) > 3:
                    # Clean the text to make a valid filename
                    clean_text = re.sub(r'[^\w\s-]', '', link_text)
                    clean_text = re.sub(r'[-\s]+', '_', clean_text)

                    # Get file extension from URL
                    ext = os.path.splitext(url_filename)[1]
                    filename = f"{clean_text}{ext}"
                else:
                    filename = url_filename

                download_links.append((absolute_url, filename))

        # Remove duplicates
        download_links = list(set(download_links))

        print(f"\n[OK] Found {len(download_links)} downloadable files")
        return download_links

    def download_file(self, url, filename):
        """
        Download a single file

        Args:
            url: URL of the file to download
            filename: Name to save the file as

        Returns:
            True if successful, False otherwise
        """
        filepath = self.download_dir / filename

        # Skip if file already exists
        if filepath.exists():
            print(f"[SKIP] Skipping (already exists): {filename}")
            return True

        try:
            print(f"[DL] Downloading: {filename}")
            response = self.session.get(url, verify=False, timeout=60, stream=True)
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))

            # Download with progress
            with open(filepath, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            done = int(50 * downloaded / total_size)
                            print(f"\r  Progress: [{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} bytes", end='')
                    print()  # New line after progress

            print(f"[OK] Downloaded: {filename} ({os.path.getsize(filepath)} bytes)")
            return True

        except Exception as e:
            print(f"[ERROR] Error downloading {filename}: {e}")
            # Remove partial file if exists
            if filepath.exists():
                filepath.unlink()
            return False

    def download_all(self):
        """Main method to download all files"""
        print("=" * 70)
        print("World Taekwondo Result Book Downloader")
        print("=" * 70)

        # Get page content
        html_content = self.get_page_content()
        if not html_content:
            print("\n[ERROR] Failed to fetch page content. Exiting.")
            return

        # Extract download links
        download_links = self.extract_download_links(html_content)

        if not download_links:
            print("\n[ERROR] No downloadable files found on the page.")
            print("  This could mean:")
            print("  - The page structure is different than expected")
            print("  - Files are loaded dynamically with JavaScript")
            print("  - The URL is incorrect")
            return

        # Show what will be downloaded
        print("\nFiles to download:")
        for i, (url, filename) in enumerate(download_links, 1):
            print(f"  {i}. {filename}")

        # Download each file
        print(f"\nDownloading to: {self.download_dir.absolute()}")
        print("-" * 70)

        successful = 0
        failed = 0

        for url, filename in download_links:
            if self.download_file(url, filename):
                successful += 1
            else:
                failed += 1

            # Be nice to the server
            time.sleep(1)

        # Summary
        print("\n" + "=" * 70)
        print(f"Download Summary:")
        print(f"  [OK] Successful: {successful}")
        print(f"  [ERROR] Failed: {failed}")
        print(f"  [FOLDER] Saved to: {self.download_dir.absolute()}")
        print("=" * 70)


def main():
    # URL of the World Taekwondo RECORD&STATS page
    url = "https://www.worldtaekwondo.org/competitions/RECORD&STATS/contents"

    # Alternative: You can also try the main competition page
    # url = "https://www.worldtaekwondo.org/competition/competition_index.html"

    # Initialize downloader
    downloader = TaekwondoDownloader(url, download_dir="result_books")

    # Download all files
    downloader.download_all()


if __name__ == "__main__":
    main()
