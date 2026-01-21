"""
World Taekwondo Result Book Downloader v2
Downloads all result books from the World Taekwondo website
Searches multiple sources including wp-content/uploads and competition pages
"""

import os
import re
import time
import urllib3
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

# Disable SSL warnings (use with caution)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaekwondoDownloaderV2:
    def __init__(self, download_dir="result_books"):
        """
        Initialize the downloader

        Args:
            download_dir: Directory to save downloaded files
        """
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

        self.downloaded_urls = set()

    def get_page_content(self, url):
        """Fetch the page content"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            print(f"  [OK] Status: {response.status_code}")
            return response.text
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    def extract_pdf_links_from_page(self, url, html_content):
        """
        Extract PDF and document links from a page

        Args:
            url: The URL of the page (for making absolute URLs)
            html_content: HTML content of the page

        Returns:
            List of tuples (url, filename)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        download_links = []

        # Look for downloadable files
        file_extensions = ['.pdf', '.PDF', '.doc', '.docx', '.xls', '.xlsx', '.zip']

        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Check if it's a downloadable file
            if any(ext in href for ext in file_extensions):
                # Make absolute URL
                absolute_url = urljoin(url, href)

                # Skip if already downloaded
                if absolute_url in self.downloaded_urls:
                    continue

                # Try to get a descriptive filename
                link_text = link.get_text(strip=True)

                # Extract filename from URL
                parsed_url = urlparse(absolute_url)
                url_filename = os.path.basename(parsed_url.path)

                # Use link text as filename if available, otherwise use URL filename
                if link_text and len(link_text) > 3 and not link_text.startswith('http'):
                    # Clean the text to make a valid filename
                    clean_text = re.sub(r'[^\w\s-]', '', link_text)
                    clean_text = re.sub(r'[-\s]+', '_', clean_text).strip('_')

                    # Get file extension from URL
                    ext = os.path.splitext(url_filename)[1]
                    if clean_text:
                        filename = f"{clean_text}{ext}"
                    else:
                        filename = url_filename
                else:
                    filename = url_filename

                download_links.append((absolute_url, filename))

        return download_links

    def scrape_competition_list(self, list_url):
        """
        Scrape the competition list page to find individual competition pages

        Args:
            list_url: URL of the competition list page

        Returns:
            List of competition page URLs
        """
        html_content = self.get_page_content(list_url)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        competition_urls = []

        # Find all competition links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Look for competition view pages
            if 'view.html' in href or 'competition' in href:
                absolute_url = urljoin(list_url, href)
                if absolute_url not in competition_urls:
                    competition_urls.append(absolute_url)

        return competition_urls

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
            print(f"  [SKIP] Already exists: {filename}")
            return True

        try:
            print(f"  [DL] Downloading: {filename}")
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

            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  [OK] Downloaded: {filename} ({size_mb:.2f} MB)")
            self.downloaded_urls.add(url)
            return True

        except Exception as e:
            print(f"  [ERROR] {filename}: {e}")
            # Remove partial file if exists
            if filepath.exists():
                filepath.unlink()
            return False

    def download_all(self):
        """Main method to download all files"""
        print("=" * 70)
        print("World Taekwondo Result Book Downloader v2")
        print("=" * 70)

        all_download_links = []

        # Source 1: Competition list page (mobile)
        print("\n[1] Checking mobile competition list...")
        competition_urls = self.scrape_competition_list(
            "https://m.worldtaekwondo.org/competition/list.html?mcd=A01&sc=re"
        )
        print(f"  Found {len(competition_urls)} competition pages")

        # Check each competition page for PDFs (limit to first 20 to avoid overwhelming)
        for i, comp_url in enumerate(competition_urls[:20], 1):
            print(f"\n[1.{i}] Checking competition page...")
            html = self.get_page_content(comp_url)
            if html:
                links = self.extract_pdf_links_from_page(comp_url, html)
                if links:
                    print(f"  Found {len(links)} files")
                    all_download_links.extend(links)
            time.sleep(0.5)  # Be nice to the server

        # Source 2: Desktop competition list
        print("\n[2] Checking desktop competition list...")
        html = self.get_page_content("https://www.worldtaekwondo.org/competition/list.html?mcd=A01&sc=re")
        if html:
            links = self.extract_pdf_links_from_page(
                "https://www.worldtaekwondo.org/competition/list.html?mcd=A01&sc=re",
                html
            )
            all_download_links.extend(links)

        # Source 3: Documents page
        print("\n[3] Checking documents page...")
        html = self.get_page_content("http://www.worldtaekwondo.org/documents-wt/docu.html?cd1=06")
        if html:
            links = self.extract_pdf_links_from_page(
                "http://www.worldtaekwondo.org/documents-wt/docu.html?cd1=06",
                html
            )
            all_download_links.extend(links)

        # Source 4: Known result books from wp-content
        print("\n[4] Adding known result book URLs...")
        known_pdfs = [
            ("http://www.worldtaekwondo.org/wp-content/uploads/2015/11/2013_WTF_World_Taekwondo_Championships.pdf",
             "2013_WTF_World_Taekwondo_Championships.pdf"),
        ]
        all_download_links.extend(known_pdfs)

        # Remove duplicates
        all_download_links = list(set(all_download_links))

        if not all_download_links:
            print("\n[ERROR] No downloadable files found.")
            return

        # Show what will be downloaded
        print("\n" + "=" * 70)
        print(f"Total files found: {len(all_download_links)}")
        print("=" * 70)

        # Download each file
        print(f"\nDownloading to: {self.download_dir.absolute()}")
        print("-" * 70)

        successful = 0
        failed = 0

        for url, filename in all_download_links:
            print(f"\n[{successful + failed + 1}/{len(all_download_links)}] {filename}")
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
    # Initialize downloader
    downloader = TaekwondoDownloaderV2(download_dir="result_books")

    # Download all files
    downloader.download_all()


if __name__ == "__main__":
    main()
