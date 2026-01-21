# Taekwondo Scraper - Fix for 400/403 Errors

## ⚠️ URGENT: Original Scraper No Longer Works

If you're seeing errors like:
```
[ERROR] 400 Client Error: 400 for url: https://www.worldtaekwondo.org/competition/ranking.html?gender=M&weight=1
[ERROR] 400 Client Error: 400 for url: https://www.worldtaekwondo.org/athlete/list.html?country=KSA
```

**Your `taekwondo_scraper.py` is now outdated.**

## What Happened

World Taekwondo completely restructured their website:

| Old (Broken) | New (Working) |
|-------------|---------------|
| `/competition/ranking.html` | `/athletes/Ranking/contents` |
| `/athlete/list.html` | SimplyCompete iframe |
| Static HTML pages | JavaScript-loaded iframes |
| Direct API access | Protected SimplyCompete API |

## ✅ BEST SOLUTION: Use the Master Smart Scraper

### 🌟 Recommended: Run Everything with Smart Updates

```bash
# First time - Full scrape from 2015
python scrape_all_data.py --force-full

# Daily updates - Automatically detects what needs updating
python scrape_all_data.py

# Force full refresh weekly
python scrape_all_data.py --force-full --year-from 2020
```

**What it does:**
- ✅ Runs ALL scraping methods automatically
- ✅ Smart update: only scrapes new data since last run
- ✅ Tracks scraping history in `.scrape_metadata.json`
- ✅ Auto-detects: full scrape (if >7 days) or incremental update
- ✅ Shows detailed summary with file counts and sizes

### Alternative: Individual Scrapers

#### For Current Rankings & Data:

```bash
# Install Selenium (if not already installed)
pip install selenium webdriver-manager

# Run the updated Selenium scraper
python taekwondo_scraper_selenium.py --headless
```

### For Downloadable Files:

```bash
# Find and download all Excel/PDF files
python download_all_taekwondo_data.py --year-from 2015
```

### Test What's Working:

```bash
# Diagnostic tool
python quick_test.py
```

## Files to Use

| File | Status | Purpose |
|------|--------|---------|
| ✅ `taekwondo_scraper_selenium.py` | **USE THIS** | Browser automation - gets all data |
| ✅ `download_all_taekwondo_data.py` | **USE THIS** | Downloads available files |
| ✅ `quick_test.py` | **USE THIS** | Tests endpoints |
| ⚠️ `taekwondo_scraper.py` | **BROKEN** | Original scraper - outdated |
| ⚠️ `taekwondo_scraper_updated.py` | **BLOCKED** | API approach - returns 403 |

## Example: Get Saudi Athletes

### Old Way (Broken):
```python
# ❌ This returns 400 error:
url = "https://www.worldtaekwondo.org/athlete/list.html?country=KSA"
```

### New Way (Working):
```python
# ✅ Use Selenium scraper:
from taekwondo_scraper_selenium import TaekwondoSeleniumScraper

scraper = TaekwondoSeleniumScraper()
rankings_df = scraper.scrape_rankings_page()
# Data extracted from iframe
```

## How to Get All Historical Data

The new website structure means you need to:

1. **Use Selenium** to access the SimplyCompete iframes
2. **Iterate through dates** by modifying iframe parameters
3. **Extract data** from each month/year combination

### Example Enhancement for Historical Data:

```python
# Modify taekwondo_scraper_selenium.py to loop through dates:
from selenium import webdriver
from datetime import datetime

driver = webdriver.Chrome()

for year in range(2015, 2026):
    for month in range(1, 13):
        # Navigate to rankings page with specific month/year
        iframe_url = f"https://worldtkd.simplycompete.com/rankingsV2?year={year}&month={month}&embedded=true"

        # Switch to iframe and extract data
        driver.switch_to.frame(iframe_element)
        # ... extract table data ...
        driver.switch_to.default_content()
```

## Successfully Downloaded

✅ We successfully downloaded:
- `World_Para_Poomsae_Ranking_May_2025.xlsx` (39 athletes)

This proves downloadable files exist, but they're limited.

## Why SimplyCompete API is Blocked

The data platform blocks direct access:

```python
# ❌ This returns 403 Forbidden:
requests.get("https://worldtkd.simplycompete.com/rankingsV2?...")
# Error: 403 Forbidden

# ✅ This works (Selenium with browser cookies/session):
driver.get("https://www.worldtaekwondo.org/athletes/Ranking/contents")
# Browser handles authentication automatically
```

## Alternative: Manual Data Collection

If automation doesn't work:

1. **Visit:** https://www.worldtaekwondo.org/athletes/Ranking/contents
2. **Wait for iframe to load** the ranking table
3. **Export manually** or take screenshots
4. **Repeat for each category/date** you need

## Integration with Existing System

To integrate with your existing `performance_analyzer.py` and `dashboard.py`:

1. **Run Selenium scraper** to collect data:
   ```bash
   python taekwondo_scraper_selenium.py
   ```

2. **Data saved to `data/` directory** in same format as before

3. **Continue using existing analysis tools**:
   ```bash
   python performance_analyzer.py
   streamlit run dashboard.py
   ```

## Next Steps

1. **Replace in `taekwondo_scraper.py`:**
   - Comment out old scraping logic
   - Call `taekwondo_scraper_selenium.py` instead

2. **Update `agents.py`** to use new scrapers:
   ```python
   # Instead of:
   # scraper = TaekwondoDataScraper()

   # Use:
   from taekwondo_scraper_selenium import TaekwondoSeleniumScraper
   scraper = TaekwondoSeleniumScraper(headless=True)
   ```

3. **Test full workflow:**
   ```bash
   python taekwondo_scraper_selenium.py --headless
   python performance_analyzer.py
   streamlit run dashboard.py
   ```

## Support

For detailed technical explanation, see:
- `SOLUTION_SUMMARY.md` - Complete technical analysis
- `README.md` - Original system documentation

---

**Fix Created:** 2025-11-12
**Status:** ✅ Solution implemented and tested
**Action Required:** Switch to Selenium-based scraper
