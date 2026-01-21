# Quick Start Guide - Taekwondo Data Collection

## 🚀 Get Started in 3 Steps

### Step 1: Install Selenium (Optional but Recommended)

```bash
pip install selenium webdriver-manager
```

### Step 2: Run the Master Scraper

```bash
# First time - collect all historical data
python scrape_all_data.py --force-full
```

This will:
- ✅ Test all endpoints
- ✅ Download available Excel/PDF files
- ✅ Scrape current rankings using Selenium
- ✅ Save metadata for future smart updates

**Time:** 5-15 minutes for full scrape

### Step 3: Daily Updates

```bash
# Run daily - automatically only updates new data
python scrape_all_data.py
```

This will:
- ✅ Auto-detect if incremental or full update needed
- ✅ Only scrape data since last run (fast!)
- ✅ Track all scraping history

**Time:** 1-3 minutes for incremental updates

---

## 📊 What You'll Get

After running, you'll have data in these directories:

```
Taekwondo/
├── data/
│   ├── rankings/          # Ranking files
│   ├── competitions/      # Competition data
│   └── athletes/          # Athlete profiles
├── taekwondo_data/        # Downloaded files
│   ├── rankings/
│   ├── competitions/
│   └── downloads/
└── .scrape_metadata.json  # Tracking file (auto-created)
```

## 🔄 Update Modes

### Automatic Smart Updates (Recommended)
```bash
python scrape_all_data.py
```

**The script automatically decides:**
- **First run:** Full scrape from 2015
- **<7 days since last:** Incremental update (only new data)
- **>7 days since last:** Full refresh

### Force Full Scrape
```bash
python scrape_all_data.py --force-full
```

### Custom Year Range
```bash
# Full scrape from 2020 onwards
python scrape_all_data.py --force-full --year-from 2020
```

## 📅 Recommended Schedule

### Option 1: Daily Automation (Best for Active Monitoring)
Set up a scheduled task to run daily:

**Windows Task Scheduler:**
```bash
# Create a task that runs daily at 6:00 AM
python scrape_all_data.py
```

**Linux/Mac Cron:**
```bash
# Add to crontab (6 AM daily)
0 6 * * * cd /path/to/Taekwondo && python scrape_all_data.py
```

### Option 2: Manual Weekly Updates
```bash
# Run once per week
python scrape_all_data.py
```

## 🎯 After Scraping - Analyze Data

### 1. Run Performance Analysis
```bash
python performance_analyzer.py
```

### 2. Launch Dashboard
```bash
streamlit run dashboard.py
```

Then open browser to: `http://localhost:8501`

## 📝 Scraping Summary

Each run shows:
- 🔄 Mode (Full or Incremental)
- ⏱️ Time taken
- 📁 Files downloaded
- 🔢 Total scrapes performed
- ⚠️ Any errors/warnings

Example output:
```
╔══════════════════════════════════════════════════════════════════╗
║               TAEKWONDO MASTER DATA SCRAPER                      ║
║               Smart Update System                                ║
╚══════════════════════════════════════════════════════════════════╝

⏰ Started: 2025-11-12 18:30:00

⚡ Mode: INCREMENTAL UPDATE
📅 Last Scrape: 2025-11-11 06:00:00
   (1 days ago)
📅 Update Range: 2024 - 2025

[...scraping process...]

======================================================================
  FINAL SUMMARY
======================================================================

🔄 Scrape Mode: INCREMENTAL
⏱️  Total Time: 2m 34s
📁 Files Downloaded: 15
🔢 Total Scrapes: 12

✅ All operations completed successfully!

📊 Data Locations:
   - data/: 45 files (12.3 MB)
   - taekwondo_data/: 23 files (8.7 MB)

📝 Updated Today:
   - world_rankings_20251112.csv
   - competitions_20251112.csv

🎯 Next Steps:
   1. Review collected data in data directories
   2. Run analysis: python performance_analyzer.py
   3. Launch dashboard: streamlit run dashboard.py

⏰ Next Update Recommendation:
   Run daily for continuous updates:
   python scrape_all_data.py
```

## ❓ Troubleshooting

### "Selenium not installed" warning
```bash
pip install selenium webdriver-manager
```

### Script finds no files
- World Taekwondo has limited downloadable files
- Most data is in JavaScript iframes (requires Selenium)
- Check `SCRAPER_FIX.md` for details

### Want to see what's being scraped
```bash
# Run individual test
python quick_test.py
```

## 📚 More Information

- **Full technical details:** `SOLUTION_SUMMARY.md`
- **Fix explanations:** `SCRAPER_FIX.md`
- **Original system docs:** `README.md`

---

## 🎯 Quick Command Reference

| Command | Purpose |
|---------|---------|
| `python scrape_all_data.py` | Smart update (recommended) |
| `python scrape_all_data.py --force-full` | Force full scrape |
| `python scrape_all_data.py --year-from 2020` | Full scrape from 2020 |
| `python quick_test.py` | Test endpoints |
| `python performance_analyzer.py` | Analyze collected data |
| `streamlit run dashboard.py` | Launch dashboard |

---

**Ready to start?** Run: `python scrape_all_data.py --force-full`
