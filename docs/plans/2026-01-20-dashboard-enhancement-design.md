# Taekwondo Dashboard Enhancement Design

**Date:** 2026-01-20
**Author:** Performance Analysis Team
**Status:** Approved for Implementation

---

## Executive Summary

Enhancement of the Saudi Taekwondo Performance Analytics Dashboard to support dual-track qualification strategy for **Asian Games 2026 (Nagoya)** and **LA 2028 Olympics**. Includes automated data pipeline via GitHub Actions, Azure Blob Storage, and intelligent alerting.

### Strategic Context

| Factor | Status |
|--------|--------|
| Primary Focus | Both Asian Games 2026 AND LA 2028 Olympics |
| Team Strength | Competitive - athletes in top 10 world rankings |
| Key Gaps | Asian Games context, Tactical scouting, Points simulation |
| Automation Need | Full automation with email/Slack alerts |

---

## 1. Architecture Overview

### Dual-Track Qualification Dashboard

**Core Concept:** Two parallel tracking systems with shared infrastructure:

| Track | Target | Timeline | Key Metrics |
|-------|--------|----------|-------------|
| **Asian Games 2026** | Medals in Nagoya | ~18 months | Continental rank, Asian rivals, qualification status |
| **LA 2028 Olympics** | Medals/Qualification | ~30 months | World rank, Olympic pathway, points accumulation |

### Data Flow

```
GitHub Actions (weekly)
    │
    ├── Weekly Rankings Sync (Sunday 2am UTC)
    ├── Competition Results Sync (post-event trigger)
    │
    ▼
World Taekwondo Scraper
    │
    ▼
Azure Blob Storage (Parquet format)
    │
    ├── rankings_YYYYMMDD.parquet
    ├── competitions_master.parquet
    ├── scouting_profiles.parquet
    │
    ▼
DuckDB Query Layer
    │
    ▼
Dashboard + Alert System (Email/Slack)
```

---

## 2. New Dashboard Views

### 2.1 Asian Games 2026 Command Center

**Purpose:** Dedicated view for Nagoya 2026 qualification and medal targeting.

**Components:**

1. **Qualification Status Panel**
   - Real-time qualification status per athlete
   - Asian rank vs. qualification threshold
   - Path indicator (Continental rank / Direct qualification)

2. **Asian Rivals Focus**
   - Primary: Iran (IRI), South Korea (KOR), China (CHN), Japan (JPN)
   - Regional: Jordan (JOR), Uzbekistan (UZB), Thailand (THA), Kazakhstan (KAZ)
   - Head-to-head records against Asian opponents only

3. **Continental Competition Calendar**
   - Asian Championships (key qualifying event)
   - Asian Open tournaments
   - President's Cup Asia
   - Points available at each event

4. **Medal Probability Matrix**
   - Asian rank per category
   - Gap to medal positions (top 3)
   - Historical Asian Games medal winners
   - "Beatable" opponents analysis

### 2.2 Points Simulator ("What If" Engine)

**Purpose:** Simulate competition attendance decisions and projected outcomes.

**Components:**

1. **Competition Selection Interface**
   - Checkbox list of upcoming competitions
   - Points available at each tier
   - Cost estimates per event

2. **Scenario Builder**
   - Best case / Realistic / Worst case finish inputs
   - Points calculation per scenario

3. **Projection Output**
   - Current vs. Projected world rank
   - Points change visualization
   - Asian Games qualification impact
   - LA 2028 qualification probability change

4. **Cost-Benefit Analysis**
   - Total cost per scenario
   - Expected points gained
   - ROI score calculation
   - Recommendation engine

**Algorithm:**
- Uses WT 2-year rolling points decay formula
- Factors in points expiring in next 12 months
- Calculates rank change based on projected points vs. competitors

### 2.3 Tactical Scouting Hub

**Purpose:** Deep opponent intelligence for match preparation.

**Components:**

1. **Opponent Profile Cards**
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │ ATHLETE NAME (Country)                      World Rank: #X  │
   │ Category | Age | Height | Reach                             │
   ├─────────────────────────────────────────────────────────────┤
   │ FIGHTING STYLE: [Tag] | [Stance]                            │
   │ SIGNATURE TECHNIQUES: [List]                                │
   │ WEAKNESSES: [Notes]                                         │
   ├─────────────────────────────────────────────────────────────┤
   │ vs KSA ATHLETES: [Head-to-head records]                     │
   ├─────────────────────────────────────────────────────────────┤
   │ VIDEO LINKS | COACH NOTES                                   │
   └─────────────────────────────────────────────────────────────┘
   ```

2. **Scouting Database Fields**
   | Field | Type | Source |
   |-------|------|--------|
   | Fighting style | Tag (Counter/Aggressive/Mixed) | Manual |
   | Stance | Orthodox/Southpaw | Manual |
   | Signature techniques | Multi-select tags | Manual |
   | Weaknesses | Free text | Coach notes |
   | Video links | URLs | YouTube/archives |
   | Injury notes | Text + date | Intelligence |
   | Coach/training base | Text | Research |

3. **Pre-Competition Report Generator**
   - Auto-generates PDF with potential opponents
   - Head-to-head history
   - Style matchup analysis
   - Recommended game plan

4. **"Who Beats Who" Network**
   - Visual graph of opponent relationships
   - Nemesis identification
   - Common opponent comparison

### 2.4 Dual-Track Timeline

**Purpose:** Visual Gantt chart showing both qualification paths with key milestones.

**Components:**
- Asian Games 2026 track (top)
- LA 2028 Olympics track (bottom)
- Competition markers
- Qualification deadlines
- Current position indicators

---

## 3. GitHub Actions Automation

### 3.1 Workflow Files

**`weekly-rankings-sync.yml`**
- Schedule: Sunday 2am UTC
- Actions: Scrape rankings, upload to Azure, check for changes

**`competition-results-sync.yml`**
- Trigger: Manual (workflow_dispatch) after major events
- Actions: Scrape specific competition results

**`alert-check.yml`**
- Trigger: After each sync workflow
- Actions: Compare with previous data, send alerts if thresholds met

### 3.2 Alert Triggers

| Trigger | Threshold | Channel |
|---------|-----------|---------|
| KSA rank improves | Any improvement | Email + Slack |
| KSA rank drops | ≥3 positions | Email + Slack |
| Rival overtakes KSA | Direct position swap | Email |
| New competition results | KSA athlete competed | Email |
| Qualification status change | Any change | Email + Slack |

### 3.3 Alert Message Format

```
🥋 TAEKWONDO RANKING ALERT - KSA

[CHANGE TYPE] DETECTED:

Athlete: [Name]
Category: [Category]
Previous Rank: #X → New Rank: #Y (+/- Z)
Points: X → Y

Impact:
• Asian Games: [Status]
• LA 2028: [Probability change]

Triggered by: [Event/Date]

---
Saudi Taekwondo Analytics | Automated Alert
```

### 3.4 GitHub Secrets Required

| Secret Name | Purpose |
|-------------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Blob storage access |
| `SENDGRID_API_KEY` | Email alerts |
| `SLACK_WEBHOOK_URL` | Slack notifications |

---

## 4. File Structure

### New Files to Create

```
Taekwondo/
├── .github/
│   └── workflows/
│       ├── weekly-rankings-sync.yml
│       ├── competition-results-sync.yml
│       └── alert-check.yml
│
├── blob_storage.py              # Azure Blob + DuckDB
├── sync_rankings.py             # GitHub Actions entry point
├── alert_system.py              # Email + Slack alerts
│
├── dashboard.py                 # ENHANCED with 4 new views
│
├── points_simulator.py          # What-if scenario engine
├── scouting_manager.py          # Opponent profile CRUD
│
├── models.py                    # ENHANCED
│   ├── ScoutingProfile          # NEW dataclass
│   ├── SimulationScenario       # NEW dataclass
│   └── AlertEvent               # NEW dataclass
│
└── config.py                    # ENHANCED
    ├── ASIAN_RIVALS             # NEW constant
    ├── ASIAN_GAMES_CATEGORIES   # NEW constant
    └── ALERT_CONFIG             # NEW constant
```

### Enhanced Dashboard Navigation

```
Current (7 views):                    Enhanced (11 views):
─────────────────                     ──────────────────────
1. Team Overview                      1. Team Overview
2. Athlete Analysis                   2. Athlete Analysis
3. Rival Comparison                   3. Rival Comparison (Global)
4. Medal Opportunities                4. Medal Opportunities
5. Olympic Qualification              5. Olympic Qualification (LA 2028)
6. Ranking Trends                     6. Ranking Trends
7. Competition Planning               7. Competition Planning
                                      ────────────────────── NEW
                                      8. Asian Games 2026
                                      9. Points Simulator
                                      10. Tactical Scouting
                                      11. Dual-Track Timeline
```

---

## 5. Dependencies

### New Requirements

```
# Add to requirements.txt
azure-storage-blob>=12.19.0
azure-identity>=1.15.0
duckdb>=0.9.0
pyarrow>=14.0.0
slack-sdk>=3.21.0
```

---

## 6. Implementation Plan

### Phase 1: Automation Foundation
- [ ] Create `blob_storage.py` (Azure + DuckDB integration)
- [ ] Create `sync_rankings.py` (scraper for GitHub Actions)
- [ ] Create `.github/workflows/weekly-rankings-sync.yml`
- [ ] Configure GitHub secrets
- [ ] Test weekly sync

### Phase 2: Alert System
- [ ] Create `alert_system.py` (Email + Slack)
- [ ] Create `.github/workflows/alert-check.yml`
- [ ] Configure SendGrid and Slack webhook
- [ ] Test alert triggers

### Phase 3: Asian Games Command Center
- [ ] Add `ASIAN_RIVALS` to `config.py`
- [ ] Add Asian Games view to `dashboard.py`
- [ ] Create Asian qualification tracking logic
- [ ] Add continental competition calendar

### Phase 4: Points Simulator
- [ ] Create `points_simulator.py`
- [ ] Add `SimulationScenario` to `models.py`
- [ ] Add Points Simulator view to `dashboard.py`
- [ ] Implement ROI calculation algorithm

### Phase 5: Tactical Scouting Hub
- [ ] Create `scouting_manager.py`
- [ ] Add `ScoutingProfile` to `models.py`
- [ ] Add Tactical Scouting view to `dashboard.py`
- [ ] Implement scouting report PDF generator

### Phase 6: Dual-Track Timeline
- [ ] Add timeline visualization to `dashboard.py`
- [ ] Create milestone tracking
- [ ] Link to qualification probability

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Data freshness | Rankings updated within 24 hours of WT publication |
| Alert latency | Notifications within 1 hour of data change |
| Simulator accuracy | Rank projections within ±2 positions |
| Scouting coverage | Profiles for all top 20 opponents per category |
| User adoption | Coaches using dashboard weekly |

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| WT website structure changes | Scraper diagnostic agent, fallback to manual |
| Azure free tier limits | Monitor usage, archive old data |
| Alert fatigue | Configurable thresholds, digest mode option |
| Data quality issues | Validation layer, quality scoring |

---

## Appendix: Team Saudi Brand Colors

All new views will use the established Saudi Olympic Committee theme:

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Teal | `#007167` | Headers, primary buttons, positive indicators |
| Gold Accent | `#a08e66` | Highlights, PB markers, secondary accents |
| Dark Teal | `#005a51` | Hover states, gradients |
| Light Teal | `#009688` | Secondary positive |
| Gray Blue | `#78909C` | Neutral, needs improvement |

---

*Document approved for implementation on 2026-01-20*
