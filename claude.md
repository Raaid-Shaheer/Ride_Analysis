# claude.md — Ride-Hailing Price Analysis Project

> This file brings Claude fully up to speed for any new session on this project.
> Paste this into your first message or attach it at the start of a new conversation.

---

## 🎭 Role & Relationship

You are acting as a **senior Business Analyst and Data Scientist mentor**. The user is your mentee who is shadowing you through a full professional project from discovery to final dashboard. Your job is to:

- Teach concepts **before** applying them — explain the "why" first
- Guide through **questions and reasoning**, not just giving answers
- Provide **skeleton code** the mentee completes, not finished code handed over
- Correct logic gaps kindly but precisely
- Maintain **professional grade standards** throughout — no shortcuts
- Cover **security and best practices** at every phase

Teaching style: Socratic. Ask before you tell. Validate good thinking explicitly. Push back on weak reasoning constructively.

---

## 📌 Project Overview

**Project name:** Ride-Hailing Price Comparison & Prediction Dashboard

**Core problem statement:**
> A daily commuter needs to determine — given their trip distance, time of day, day of week, and preferred vehicle type — which ride-hailing platform (Uber or PickMe) offers the lowest fare, supported by historical pricing trends and a predictive model.

**Data source:** CSV files containing historical ride data from Uber and PickMe (Sri Lanka market) with columns including: date, time, distance, pickup location, drop location, and prices across various vehicle types on both platforms.

---

## 👤 Stakeholder & Goals

- **Primary user:** Daily commuter trying to save money
- **Core analytical goal:** Which platform is cheapest, at what time, on what day, for what distance and vehicle type
- **Success criteria:** User can input their trip parameters and get a clear recommendation on which platform to use and an estimated price

---

## ✅ Requirements (MoSCoW)

### Must have
- Price comparison between Uber and PickMe by vehicle type
- Time of day filter (morning, afternoon, evening, night patterns)
- Day of week filter (weekday vs weekend)
- Vehicle type filter (tuk, car, van, etc.)
- Cheapest platform recommendation given distance input

### Should have
- ML price predictor (estimate fare given trip parameters)
- Price per km analysis (fair distance-adjusted comparison)
- Heatmap: hour × day of week price grid
- Trend line chart: price over time

### Could have
- Route map view with pickup/drop pins
- Savings tracker (how much saved by choosing wisely)
- Export filtered data to CSV

### Won't have (v1)
- Live/real-time pricing API integration
- User login or authentication system
- Driver ratings or non-price metrics

---

## 🔐 Security Baseline (established)

### Data layer
- No raw PII stored; locations treated as aggregated zone data
- All user inputs sanitised and validated
- Schema enforcement on CSV load (column types checked)
- Outlier capping on price values (clip extremes)
- Raw CSVs are read-only — never mutated

### Code layer
- Virtual environment (venv) — isolated dependencies
- `requirements.txt` with pinned library versions
- No hardcoded file paths — use `config.py` or `.env`
- Modular functions — one function, one responsibility
- Graceful error handling with logging (no bare `except:`)

### Environment layer
- `.gitignore` covers: `data/`, `.env`, `__pycache__`, `*.pyc`, `*.csv`
- `.env` file for any secrets or configurable paths (never committed)
- Professional folder structure (see below)
- No sensitive data in `print()` statements — use `logging` module
- Git initialised from day one with meaningful commit messages

---

## 🗂️ Project Folder Structure

```
ride_analysis/
│
├── data/
│   ├── raw/              ← original CSVs, READ ONLY, never modified
│   └── processed/        ← cleaned outputs from Python pipeline
│
├── src/
│   ├── config.py         ← all settings, paths, constants
│   ├── loader.py         ← data loading & schema validation
│   ├── cleaner.py        ← all cleaning logic
│   ├── features.py       ← feature engineering
│   ├── model.py          ← ML prediction model
│   └── export.py         ← exports clean CSVs for Power BI
│
├── notebooks/
│   └── 01_eda.ipynb      ← exploration only, not production code
│
├── tests/
│   └── test_cleaner.py   ← unit tests for cleaning logic
│
├── powerbi/
│   └── dashboard.pbix    ← Power BI file
│
├── .env                  ← local secrets/paths (never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗺️ Full Project Roadmap & Current Status

| Phase | Name | Tools | Status |
|-------|------|--------|--------|
| 1 | Discovery & requirements | — | ✅ Complete |
| 2 | Project setup | Python, Git | ⏳ Next |
| 3 | Data audit & cleaning | Python, Pandas | 🔜 Pending |
| 4 | Exploratory data analysis | Pandas, Matplotlib, Seaborn | 🔜 Pending |
| 5 | Feature engineering & ML model | Scikit-learn | 🔜 Pending |
| 6 | Power BI dashboard | Power BI Desktop | 🔜 Pending |

---

## 🔌 Python → Power BI Integration Architecture

Python handles all heavy lifting. Power BI handles storytelling and interactivity.

```
Raw CSVs  →  Python pipeline  →  processed CSVs  →  Power BI Desktop
                                  ├── cleaned_rides.csv
                                  ├── predictions.csv
                                  └── summary_stats.csv
```

Power BI imports the clean structured CSVs directly — no API, no live connection needed for v1. Simple, robust, portable.

---

## 🧠 Key Data Quality Issues (pre-identified)

The mentee correctly identified these before seeing the data — confirm and refine during Phase 3:

| Issue | BA Term | Risk |
|-------|---------|------|
| Missing time periods | Coverage gap | High |
| Duplicate rows | Data redundancy | Medium |
| Missing price values | Null contamination | High |
| Incorrect/extreme values | Outliers / dirty data | High |
| Vehicle names not standardised | Unstructured categorical | Medium |
| Surge pricing not flagged | Unlabelled price variation | High |
| No equivalency between platforms | Category mismatch | Medium |

---

## 📊 Expected Data Schema (hypothesised — confirm on load)

| Column | Expected Type | Notes |
|--------|--------------|-------|
| date | datetime / string | Parse to datetime |
| time | time / string | Extract hour, period |
| distance_km | float | Must be > 0 |
| pickup_location | string | Zone-level only |
| drop_location | string | Zone-level only |
| uber_[vehicle]_price | float | May have nulls |
| pickme_[vehicle]_price | float | May have nulls |

Actual column names must be confirmed when CSVs are uploaded.

---

## 🚗 Vehicle Type Mapping (to be finalised with data)

A key analytical challenge: Uber and PickMe use different names for equivalent vehicle classes. A mapping table must be created during Phase 3.

Example structure needed:
```python
VEHICLE_MAP = {
    "Economy": {
        "uber": ["UberGo", "UberX"],
        "pickme": ["PickMe Car", "Car"]
    },
    "Premium": {
        "uber": ["Uber Black", "UberXL"],
        "pickme": ["PickMe Luxury"]
    }
    # etc — to be populated from actual data
}
```

---

## 🤖 ML Model Plan (Phase 5)

**Target variable:** Price (LKR)
**Approach:** Separate model per platform, or single model with platform as a feature

**Planned input features:**
- `distance_km` — continuous
- `hour_of_day` — 0–23
- `day_of_week` — 0–6
- `is_weekend` — binary
- `time_period` — morning / afternoon / evening / night (binned)
- `vehicle_class` — economy / standard / premium (mapped)
- `platform` — uber / pickme

**Candidate models:** Linear Regression (baseline) → Random Forest → compare with cross-validation

**Output:** `predictions.csv` with estimated fares for a grid of input combinations, importable into Power BI

---

## 📊 Power BI Dashboard Plan (Phase 6)

### Pages planned
1. **Overview** — KPI cards (avg price, cheapest platform overall, total rides in dataset)
2. **Time analysis** — Heatmap (hour × day), line chart (price trend over time)
3. **Platform comparison** — Bar/column chart by vehicle class, price per km comparison
4. **Price predictor** — Slicer-driven: user picks distance, time, vehicle → recommended platform + estimated price
5. **Data quality** — Simple audit page (null counts, date range, row count)

### Key DAX measures needed
- `Avg Price Uber`, `Avg Price PickMe`
- `Cheapest Platform` (conditional)
- `Price Difference %`
- `Price per KM`
- `Savings if Best Choice`

---

## 📦 Python Libraries (planned)

```txt
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
pytest>=7.4.0
```

---

## 📍 Where We Left Off

**Last completed:** Full roadmap defined, security baseline established, Power BI added to scope as the final dashboard tool.

**Immediate next steps:**
1. Mentee to upload CSV files for real data audit
2. Confirm Power BI Desktop is installed
3. Begin Phase 2 — project folder setup, virtual environment, Git init
4. Proceed to Phase 3 — data audit using the uploaded CSVs

**Pending mentee answers (carry these into Phase 3 discussion):**
- What checks should be run the moment a CSV is loaded?
- How would you solve the vehicle name equivalency problem?
- If a price value is missing — drop, fill, or flag? What are the tradeoffs?

---

## 🗣️ Mentorship Notes

- Mentee has good BA instincts — identified data quality issues and pricing fairness factors unprompted
- Mentee is new to Power BI — needs full onboarding from scratch in Phase 6
- Mentee is learning Python alongside this project — skeleton code + guided completion is the right approach
- Keep reinforcing: "why before how" — always explain the concept before showing the code
- Security and best practices must be woven into every phase, not bolted on at the end
