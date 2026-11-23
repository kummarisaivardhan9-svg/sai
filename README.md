# 🌿 Campus Catalyst: Carbon Footprint Awareness Calculator
**Project #48: Carbon Footprint Awareness Calculator | Domain: Environment & Sustainability**  
*Hackathon Mentor Guide Conformance & Full Web Stack (HTML5, CSS3, Vanilla JS, Python)*

---

## 🚀 Overview

**Campus Catalyst** is a software application and web platform engineered to estimate personal and institutional carbon footprints from user-entered travel and living habits. Built with strict defensive validation, real-time formula computation based on **IPCC 2026** and **GHG Protocol** standards, and fault-tolerant local persistence (surviving restarts via JSON and CSV).

### 🌟 Key Highlights
1. **Interactive Web Application & Login System** (Built with **HTML5, CSS3, Vanilla JavaScript**):
   - **Dedicated Login / Sign Up Page** (`static/login.html` & `/#login`) with 1-click Demo Fill credentials for Students, Faculty, and Sustainability Auditors.
   - **Real-Time Reactive Calculator**: Sliders and inputs update the calculated $CO_2e$ footprint live without page reloads.
   - **Threshold Warning Indicators**: Real-time warning banners alert users when their footprint exceeds the campus benchmark ceiling ($>450\text{ kg CO}_2\text{e/mo}$).
   - **Executive Analytics Dashboard**: High-DPI offline Canvas charts for emission breakdowns, monthly trends, and ecological status distributions.
   - **Historical Records Query & Search**: Filter by keyword, campus role, ecological status, and sort by highest/lowest emissions.
   - **Bulk CSV Dataset Ingestion**: Drag-and-drop CSV uploader with row-by-row defensive validation and detailed error diagnostics.
   - **Multi-Format Summary Exporters**: Direct downloads for structured **Markdown reports (.md)**, **Standardized CSV (.csv)**, and **Plain-Text Audit Logs (.txt)**.
2. **Interactive Terminal Interface (CLI)** (`cli_calculator.py`):
   - Full ANSI-colored menu prompt with defensive input loops, query search, and summary table exports.
3. **50-Record Pre-Seeded Dataset** (`data/sample_dataset_50.csv`):
   - Rich campus cohort entries including normal users, boundary limits, and edge conditions.

---

## 📁 Project Architecture

```
hacker sai/
├── app.py                      # Python HTTP server & REST API (pure Python standard library)
├── business_logic.py           # Core computation, defensive validation, persistence, auth & exporters
├── cli_calculator.py           # Interactive ANSI terminal CLI interface
├── seed_data.py                # 50-record dataset generator & initial database seeder
├── test_calculator.py          # Unit & integration test suite (14 passing tests)
├── data/
│   ├── users.json              # Persistent user credentials (SHA-256 + salt hashed)
│   ├── footprint_records.json  # Persistent JSON records
│   ├── footprint_records.csv   # Standardized 25-column CSV export
│   └── sample_dataset_50.csv   # 50 realistic pre-seeded campus records
└── static/
    ├── index.html              # Main web portal (Calculator, Analytics, Records, Bulk Ingest, Exports)
    ├── login.html              # Dedicated full-featured Login & Registration page
    ├── css/
    │   └── style.css           # Modern responsive design system (Dark & Light themes)
    └── js/
        ├── app.js              # Frontend application logic, state, and API bindings
        └── charts.js           # Lightweight standalone Canvas/SVG charting library (zero external CDN)
```

---

## ⚡ Quick Start

### 1. Launch the Website and Login Page
To start the web server on `http://localhost:8080`:
```bash
python app.py
```
Open your browser to:
- **Main Website & Calculator:** [http://localhost:8080](http://localhost:8080)
- **Dedicated Login Page:** [http://localhost:8080/login](http://localhost:8080/login)

### 2. Demo User Credentials (1-Click Fill Available)
| Role | Username / Email | Password | Full Name |
| :--- | :--- | :--- | :--- |
| **Student** | `student_alex` / `alex@campus.edu` | `campus123` | Alex Rivera |
| **Faculty** | `prof_green` / `elena.green@campus.edu` | `campus123` | Prof. Elena Green |
| **Sustainability Auditor** | `officer_vance` / `vance@sustainability.campus.edu` | `campus123` | Dr. Marcus Vance |

*(Or click "Create Account" on the login page to register a new user!)*

### 3. Run the Interactive Terminal (CLI) Interface
```bash
python cli_calculator.py
```

### 4. Run the Automated Test Suite
```bash
python -m unittest test_calculator.py
```

---

## 🌿 Calculation Methodology & Formulae

Emissions are computed in **$\text{kg CO}_2\text{e}$** per month:

$$\text{Monthly Total } (\text{kg CO}_2\text{e}) = \text{Travel Emissions} + \text{Energy \& Living Emissions}$$

- **Travel Factors:**
  - Walking / Cycling: $0.00\text{ kg/km}$
  - Electric Vehicle: $0.053\text{ kg/km}$
  - Subway / Metro: $0.035\text{ kg/km}$
  - Campus Shuttle: $0.045\text{ kg/km}$
  - City Bus: $0.089\text{ kg/km}$
  - Hybrid Car: $0.120\text{ kg/km}$
  - Petrol Car: $0.192\text{ kg/km}$ (divided by passenger carpool count)
  - Diesel Car: $0.171\text{ kg/km}$
  - Short-Haul Flight: $+150\text{ kg}$ / flight
  - Long-Haul Flight: $+600\text{ kg}$ / flight
- **Energy Factors:**
  - Electricity: $\text{kWh} \times 0.420 \times (1 - \text{Green Share} / 100)$
  - Cooking Gas: $\text{Units} \times 2.030\text{ kg/unit}$
  - AC Cooling: $\text{Hours/day} \times 30 \times 0.60\text{ kg/hr}$
  - Heating: $\text{Hours/day} \times 30 \times 0.75\text{ kg/hr}$
  - Waste Practice: Zero Waste ($-15\text{ kg}$), Mostly Recycle ($-5\text{ kg}$), Average ($+5\text{ kg}$), High Waste ($+25\text{ kg}$)
- **Offset Trees:**
  $$\text{Trees Needed} = \left\lceil \frac{\text{Annual Tonnes} \times 1000}{21.77} \right\rceil$$
