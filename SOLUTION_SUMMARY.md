# Taekwondo Data Scraper - Solution Summary

## Problem Identified

Your original Taekwondo scrapers were failing with **400 errors** because the World Taekwondo website has undergone a complete restructure:

### What Changed:
1. **Old URL structure** (e.g., `/competition/ranking.html?gender=M&weight=1`) → **DEPRECATED** (returns 400)
2. **New structure** uses SimplyCompete external platform: `https://worldtkd.simplycompete.com`
3. **Data is loaded dynamically** via JavaScript iframes, not static HTML
4. **Direct API access is blocked** with 403 Forbidden errors

## Current Situation

### ✅ What Works:
- Main World Taekwondo website is accessible
- Rankings page loads: `https://www.worldtaekwondo.org/athletes/Ranking/contents`
- **Limited downloadable files** exist (e.g., `World_Para_Poomsae_Ranking_May_2025.xlsx`)

### ❌ What Doesn't Work:
- Old API endpoints (`/competition/ranking.html`, `/athlete/list.html`) - Return 400
- Direct SimplyCompete API access - Returns 403 Forbidden
- Most historical data is NOT available as downloadable files

## Solutions Created

### 1. **quick_test.py** - Diagnostic Tool
Tests various endpoints to check what's accessible.

**Usage:**
```bash
python quick_test.py
```

### 2. **download_all_taekwondo_data.py** - Web Crawler
Systematically searches for downloadable files across the entire website.

**Usage:**
```bash
# Download all available files from 2020 onwards
python download_all_taekwondo_data.py --year-from 2020

# Custom output directory
python download_all_taekwondo_data.py --output my_data_folder
```

**Limitations:**
- Only finds files that are directly downloadable
- Most ranking/competition data is NOT in downloadable format
- Will find Excel, PDF files where they exist

### 3. **taekwondo_scraper_selenium.py** - Browser Automation (RECOMMENDED)
Uses Selenium to access the SimplyCompete iframes and extract live data.

**Requirements:**
```bash
pip install selenium
# Also need ChromeDriver installed
```

**Usage:**
```bash
# Run with visible browser (for debugging)
python taekwondo_scraper_selenium.py

# Run headless (in background)
python taekwondo_scraper_selenium.py --headless
```

**Advantages:**
- Can access JavaScript-loaded content
- Bypasses API restrictions by using real browser
- Can extract data from iframes

## Recommended Approach for Complete Data

### Option A: Use Selenium Scraper (Most Comprehensive)
```bash
python taekwondo_scraper_selenium.py --headless
```

This will:
1. Find downloadable Excel files
2. Access SimplyCompete iframes to get live ranking data
3. Take screenshots for debugging
4. Extract table data from dynamically-loaded pages

### Option B: Manual Data Collection
Since the SimplyCompete API is heavily protected:

1. **For Rankings:**
   - Visit: `https://www.worldtaekwondo.org/athletes/Ranking/contents`
   - The iframe loads: `https://worldtkd.simplycompete.com/playerRankingV2?embedded=true`
   - You can manually export/screenshot from the iframe

2. **For Competitions:**
   - Visit: `https://www.worldtaekwondo.org/competitions/overview`
   - Browse individual competitions
   - Look for downloadable result books

### Option C: Contact World Taekwondo
For bulk historical data access:
- Email: `info@worldtaekwondo.org`
- Request official data export or API access
- Explain your use case (performance analysis for Saudi team)

## Alternative: SimplyCompete Platform

The data is hosted on: `https://worldtkd.simplycompete.com`

You might be able to:
1. Create an account on SimplyCompete
2. Request API access directly from SimplyCompete
3. Use their official export features (if available)

## Data Successfully Retrieved

From our testing, we were able to download:

### ✅ Successfully Downloaded:
- `World_Para_Poomsae_Ranking_May_2025.xlsx` (39 athletes, 8 columns)
  - Contains: Rank, Member Name, Member Number, Country, Points, Competitions, Total Points

### 📊 Data Structure:
```python
import pandas as pd
df = pd.read_excel('World_Para_Poomsae_Ranking_May_2025.xlsx')
# Shape: (39, 8)
# Columns: Rank, Member Name, Member Number, Country, Points, etc.
```

## Next Steps

### Immediate Actions:
1. **Install Selenium** (if not installed):
   ```bash
   pip install selenium webdriver-manager
   ```

2. **Run Selenium scraper** to extract iframe data:
   ```bash
   python taekwondo_scraper_selenium.py --headless
   ```

3. **Review output** in the `data/` directories

### For Historical Data (All Years):
1. The Selenium scraper can be enhanced to:
   - Iterate through different date ranges in the SimplyCompete iframe
   - Extract historical ranking data month-by-month
   - Navigate competition archives

2. **Modify the Selenium scraper** to:
   - Change iframe parameters (year, month, category)
   - Screenshot or export data for each period
   - Combine all data into comprehensive dataset

## Files Created

| File | Purpose |
|------|---------|
| `quick_test.py` | Diagnostic tool - test endpoints |
| `download_all_taekwondo_data.py` | Web crawler for downloadable files |
| `taekwondo_scraper_selenium.py` | Browser automation for iframe data |
| `taekwondo_scraper_updated.py` | API-based scraper (blocked by 403) |
| `taekwondo_comprehensive_scraper.py` | Multi-strategy scraper |

## Technical Summary

### Why Original Scraper Failed:
```python
# OLD (doesn't work anymore):
url = "https://www.worldtaekwondo.org/competition/ranking.html?gender=M&weight=1"
# Returns: 400 Bad Request

# NEW (but blocked):
url = "https://worldtkd.simplycompete.com/rankingsV2?..."
# Returns: 403 Forbidden (requires browser cookies/tokens)
```

### Why Selenium is Needed:
- SimplyCompete platform uses:
  - Session cookies
  - CORS restrictions
  - Anti-bot protections
  - JavaScript-rendered content
- Regular `requests` library can't bypass these
- Selenium simulates a real browser with full JavaScript support

## Support

If you need help:
1. Check error messages in the console output
2. Review screenshots in `data/rankings/` directory
3. Examine downloaded files in respective subdirectories

---

**Created:** 2025-11-12
**Status:** Ready for implementation
**Recommended Solution:** Selenium-based scraper for comprehensive data access
