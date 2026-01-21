"""
Taekwondo Scraper Diagnostic Agent
Intelligent web scraping agent that:
1. Diagnoses iframe extraction issues
2. Tests optimal wait times for JavaScript rendering
3. Validates data extraction from SimplyCompete rankings
4. Provides detailed logging and debugging output
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium not installed!")
    print("Install with: pip install selenium webdriver-manager")
    exit(1)


class ScraperDiagnosticAgent:
    """Intelligent agent for diagnosing and fixing scraper issues"""

    def __init__(self, headless=False, output_dir="scraper_diagnostics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.headless = headless
        self.driver = None
        self.wait = None

        # Diagnostics tracking
        self.diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'issues_found': [],
            'recommendations': []
        }

    def setup_driver(self):
        """Setup Chrome with enhanced debugging"""
        print("\n[AGENT] Setting up Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
            print("  Mode: Headless")
        else:
            print("  Mode: Visible (for debugging)")

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Enhanced logging
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--v=1')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            print("  ✓ Driver initialized successfully")
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.diagnostics['issues_found'].append(f"Driver setup failed: {e}")
            return False

    def test_rankings_iframe_extraction(self):
        """
        TEST 1: Diagnose iframe extraction issues
        Focus on the SimplyCompete rankings iframe
        """
        print("\n" + "="*70)
        print("[TEST 1] Rankings Iframe Extraction Diagnostics")
        print("="*70)

        test_result = {
            'test': 'Rankings Iframe Extraction',
            'url': 'https://www.worldtaekwondo.org/athletes/Ranking/contents',
            'status': 'unknown',
            'details': {}
        }

        try:
            # Load page
            print("\n[STEP 1] Loading rankings page...")
            self.driver.get(test_result['url'])
            time.sleep(3)
            print("  ✓ Page loaded")

            # Screenshot initial state
            screenshot_path = self.output_dir / "test1_initial_page.png"
            self.driver.save_screenshot(str(screenshot_path))
            print(f"  ✓ Screenshot saved: {screenshot_path.name}")

            # Detect iframes
            print("\n[STEP 2] Detecting iframes...")
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            print(f"  Found {len(iframes)} iframe(s)")

            test_result['details']['iframe_count'] = len(iframes)

            if len(iframes) == 0:
                test_result['status'] = 'failed'
                test_result['details']['error'] = 'No iframes found'
                self.diagnostics['issues_found'].append("Rankings page has no iframes - site structure may have changed")
                print("  ✗ No iframes found!")
                return test_result

            # Examine each iframe
            iframe_data = []
            for i, iframe in enumerate(iframes):
                iframe_info = {
                    'index': i,
                    'src': iframe.get_attribute('src'),
                    'id': iframe.get_attribute('id'),
                    'class': iframe.get_attribute('class'),
                    'width': iframe.get_attribute('width'),
                    'height': iframe.get_attribute('height')
                }
                iframe_data.append(iframe_info)

                print(f"\n  Iframe {i}:")
                print(f"    Source: {iframe_info['src']}")
                print(f"    ID: {iframe_info['id']}")
                print(f"    Class: {iframe_info['class']}")

            test_result['details']['iframes'] = iframe_data

            # Find SimplyCompete iframe
            print("\n[STEP 3] Locating SimplyCompete rankings iframe...")
            target_iframe = None
            target_index = -1

            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute('src') or ""
                if 'simplycompete' in src.lower() or 'ranking' in src.lower():
                    target_iframe = iframe
                    target_index = i
                    print(f"  ✓ Found rankings iframe at index {i}")
                    print(f"    URL: {src}")
                    break

            if target_iframe is None:
                test_result['status'] = 'failed'
                test_result['details']['error'] = 'SimplyCompete iframe not found'
                self.diagnostics['issues_found'].append("SimplyCompete iframe not detected - URL pattern may have changed")
                print("  ✗ SimplyCompete iframe not found!")
                return test_result

            # Switch to iframe
            print("\n[STEP 4] Switching to iframe context...")
            self.driver.switch_to.frame(target_iframe)
            print("  ✓ Switched to iframe")

            # Test different wait times
            print("\n[STEP 5] Testing iframe load times...")
            wait_times = [2, 5, 10, 15]
            successful_wait = None

            for wait_sec in wait_times:
                print(f"\n  Testing {wait_sec}s wait...")
                time.sleep(wait_sec)

                # Take screenshot
                screenshot_path = self.output_dir / f"test1_iframe_wait{wait_sec}s.png"
                self.driver.save_screenshot(str(screenshot_path))

                # Check for content
                tables = self.driver.find_elements(By.TAG_NAME, 'table')
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                tabs = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'tab')] | //a[contains(@class, 'tab')]")

                print(f"    Tables: {len(tables)}, Buttons: {len(buttons)}, Tabs: {len(tabs)}")

                if tables or tabs:
                    successful_wait = wait_sec
                    print(f"    ✓ Content detected after {wait_sec}s")
                    break

            if successful_wait:
                test_result['details']['optimal_wait_time'] = successful_wait
                self.diagnostics['recommendations'].append(f"Use {successful_wait}s wait time for iframe content")
            else:
                test_result['details']['optimal_wait_time'] = None
                self.diagnostics['issues_found'].append("No content detected in iframe even after 15s wait")
                print("    ✗ No content detected after multiple waits")

            # Detect tabs/navigation
            print("\n[STEP 6] Detecting navigation elements...")
            tab_selectors = [
                ("//button[contains(@class, 'tab')]", "Button with 'tab' class"),
                ("//a[contains(@class, 'tab')]", "Link with 'tab' class"),
                ("//li[contains(@class, 'tab')]", "List item with 'tab' class"),
                ("//div[contains(@class, 'tab-item')]", "Div with 'tab-item' class"),
                ("//ul[@role='tablist']//button", "Tablist button"),
                ("//ul[@role='tablist']//a", "Tablist link"),
                ("//button[contains(@onclick, 'category')]", "Button with category onclick"),
                ("//select[@id='weight-category']", "Weight category dropdown"),
            ]

            found_tabs = []
            for selector, description in tab_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"  ✓ Found {len(elements)} elements: {description}")
                        found_tabs.append({
                            'selector': selector,
                            'description': description,
                            'count': len(elements),
                            'texts': [el.text.strip()[:50] for el in elements[:5]]  # First 5
                        })
                except Exception as e:
                    pass

            test_result['details']['navigation_elements'] = found_tabs

            if found_tabs:
                print(f"\n  ✓ Total navigation patterns found: {len(found_tabs)}")
                self.diagnostics['recommendations'].append(f"Use selector: {found_tabs[0]['selector']}")
            else:
                print("\n  ✗ No navigation elements detected")
                self.diagnostics['issues_found'].append("No tabs or navigation elements found in iframe")

            # Extract sample table
            print("\n[STEP 7] Attempting table extraction...")
            tables = self.driver.find_elements(By.TAG_NAME, 'table')

            if tables:
                print(f"  Found {len(tables)} table(s)")

                for i, table in enumerate(tables[:3]):  # First 3 tables
                    try:
                        table_html = table.get_attribute('outerHTML')
                        dfs = pd.read_html(table_html)

                        if dfs and len(dfs[0]) > 0:
                            df = dfs[0]
                            print(f"\n  Table {i}: {len(df)} rows × {len(df.columns)} columns")
                            print(f"    Columns: {list(df.columns)[:5]}")

                            # Save sample
                            sample_path = self.output_dir / f"test1_table{i}_sample.csv"
                            df.to_csv(sample_path, index=False, encoding='utf-8-sig')
                            print(f"    ✓ Saved to: {sample_path.name}")

                            test_result['details'][f'table_{i}'] = {
                                'rows': len(df),
                                'columns': len(df.columns),
                                'column_names': list(df.columns)
                            }
                    except Exception as e:
                        print(f"    ✗ Error extracting table {i}: {e}")
            else:
                print("  ✗ No tables found")
                self.diagnostics['issues_found'].append("No tables detected in iframe")

            # Switch back to main context
            self.driver.switch_to.default_content()

            test_result['status'] = 'passed' if successful_wait and found_tabs else 'partial'

        except Exception as e:
            test_result['status'] = 'error'
            test_result['details']['exception'] = str(e)
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

        self.diagnostics['tests'].append(test_result)
        return test_result

    def test_competition_pages_wait_times(self):
        """
        TEST 2: Test optimal wait times for various competition pages
        """
        print("\n" + "="*70)
        print("[TEST 2] Competition Pages Wait Time Analysis")
        print("="*70)

        test_pages = [
            {
                'name': 'Olympic Games Results',
                'url': 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents',
                'expected_content': 'table'
            },
            {
                'name': 'World Championships',
                'url': 'https://www.worldtaekwondo.org/competitions/WMC/WMC_WTC/list',
                'expected_content': 'competition_list'
            },
            {
                'name': 'Grand Prix',
                'url': 'https://www.worldtaekwondo.org/competitions/WGP/WGP_WTGPS/list',
                'expected_content': 'competition_list'
            }
        ]

        test_result = {
            'test': 'Competition Pages Wait Times',
            'pages_tested': len(test_pages),
            'results': []
        }

        for page_info in test_pages:
            print(f"\n[TESTING] {page_info['name']}")
            print(f"  URL: {page_info['url']}")

            page_result = {
                'name': page_info['name'],
                'url': page_info['url'],
                'load_times': {}
            }

            try:
                # Load page
                start_time = time.time()
                self.driver.get(page_info['url'])
                initial_load = time.time() - start_time
                print(f"  Initial load: {initial_load:.2f}s")

                # Test wait times
                for wait_sec in [2, 5, 10]:
                    time.sleep(wait_sec)

                    # Check for content
                    tables = self.driver.find_elements(By.TAG_NAME, 'table')
                    links = self.driver.find_elements(By.TAG_NAME, 'a')

                    # Check for download links
                    download_links = []
                    for link in links:
                        href = link.get_attribute('href') or ""
                        if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                            download_links.append(href)

                    page_result['load_times'][f'{wait_sec}s'] = {
                        'tables': len(tables),
                        'total_links': len(links),
                        'download_links': len(download_links)
                    }

                    print(f"  After {wait_sec}s: {len(tables)} tables, {len(download_links)} download links")

                    # Screenshot
                    screenshot_path = self.output_dir / f"test2_{page_info['name'].replace(' ', '_')}_wait{wait_sec}s.png"
                    self.driver.save_screenshot(str(screenshot_path))

                page_result['status'] = 'passed'

            except Exception as e:
                page_result['status'] = 'error'
                page_result['error'] = str(e)
                print(f"  ✗ Error: {e}")

            test_result['results'].append(page_result)

        self.diagnostics['tests'].append(test_result)
        return test_result

    def test_table_extraction_methods(self):
        """
        TEST 3: Test different table extraction methods
        """
        print("\n" + "="*70)
        print("[TEST 3] Table Extraction Methods Comparison")
        print("="*70)

        # Use Olympics page as test case
        test_url = 'https://www.worldtaekwondo.org/competitions/OlympicGamesResults/contents'

        print(f"\nTest URL: {test_url}")
        self.driver.get(test_url)
        time.sleep(5)

        test_result = {
            'test': 'Table Extraction Methods',
            'url': test_url,
            'methods': []
        }

        # Method 1: pandas read_html
        print("\n[METHOD 1] Pandas read_html on table elements")
        try:
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            method1_result = {
                'method': 'Pandas read_html',
                'tables_found': len(tables),
                'tables_extracted': 0,
                'total_rows': 0
            }

            for i, table in enumerate(tables):
                try:
                    html = table.get_attribute('outerHTML')
                    dfs = pd.read_html(html)
                    if dfs and len(dfs[0]) > 0:
                        method1_result['tables_extracted'] += 1
                        method1_result['total_rows'] += len(dfs[0])
                        print(f"  Table {i}: {len(dfs[0])} rows")
                except:
                    pass

            test_result['methods'].append(method1_result)
            print(f"  ✓ Extracted {method1_result['tables_extracted']}/{method1_result['tables_found']} tables")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        # Method 2: Manual parsing
        print("\n[METHOD 2] Manual cell-by-cell extraction")
        try:
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            method2_result = {
                'method': 'Manual parsing',
                'tables_found': len(tables),
                'tables_extracted': 0,
                'total_rows': 0
            }

            for i, table in enumerate(tables[:3]):  # First 3 only
                try:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    if len(rows) > 0:
                        method2_result['tables_extracted'] += 1
                        method2_result['total_rows'] += len(rows)
                        print(f"  Table {i}: {len(rows)} rows")
                except:
                    pass

            test_result['methods'].append(method2_result)
            print(f"  ✓ Extracted {method2_result['tables_extracted']}/{method2_result['tables_found']} tables")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        self.diagnostics['tests'].append(test_result)
        return test_result

    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n" + "="*70)
        print("[DIAGNOSTIC REPORT]")
        print("="*70)

        # Issues found
        print(f"\n[ISSUES FOUND] {len(self.diagnostics['issues_found'])}")
        for i, issue in enumerate(self.diagnostics['issues_found'], 1):
            print(f"  {i}. {issue}")

        if not self.diagnostics['issues_found']:
            print("  ✓ No critical issues detected")

        # Recommendations
        print(f"\n[RECOMMENDATIONS] {len(self.diagnostics['recommendations'])}")
        for i, rec in enumerate(self.diagnostics['recommendations'], 1):
            print(f"  {i}. {rec}")

        # Save detailed report
        report_path = self.output_dir / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.diagnostics, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Detailed report: {report_path}")
        print("="*70)

        return self.diagnostics

    def run_all_diagnostics(self):
        """Run all diagnostic tests"""
        print("="*70)
        print("TAEKWONDO SCRAPER DIAGNOSTIC AGENT")
        print("Intelligent Web Scraping Diagnostics")
        print("="*70)

        if not self.setup_driver():
            print("\n[FATAL] Could not initialize WebDriver")
            return None

        try:
            # Run all tests
            self.test_rankings_iframe_extraction()
            time.sleep(2)

            self.test_competition_pages_wait_times()
            time.sleep(2)

            self.test_table_extraction_methods()

            # Generate report
            return self.generate_diagnostic_report()

        except Exception as e:
            print(f"\n[ERROR] Diagnostic agent failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                self.driver.quit()
                print("\n[CLEANUP] Browser closed")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Taekwondo Scraper Diagnostic Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This intelligent agent diagnoses and fixes scraper issues:
  1. Tests iframe extraction and optimal wait times
  2. Analyzes competition page loading behavior
  3. Compares table extraction methods
  4. Generates actionable recommendations

Examples:
  # Run with visible browser (recommended for first diagnosis)
  python scraper_diagnostic_agent.py --visible

  # Run in headless mode (faster)
  python scraper_diagnostic_agent.py
        """
    )

    parser.add_argument('--visible', action='store_true', help='Run with visible browser (for debugging)')
    parser.add_argument('--output', default='scraper_diagnostics', help='Output directory for diagnostics')

    args = parser.parse_args()

    if not SELENIUM_AVAILABLE:
        print("[ERROR] Selenium is required")
        print("Install: pip install selenium")
        return 1

    try:
        agent = ScraperDiagnosticAgent(
            headless=not args.visible,
            output_dir=args.output
        )

        diagnostics = agent.run_all_diagnostics()

        if diagnostics:
            print("\n✓ Diagnostics complete!")
            print(f"  Check '{args.output}/' for screenshots and detailed logs")
            return 0
        else:
            print("\n✗ Diagnostics failed")
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
