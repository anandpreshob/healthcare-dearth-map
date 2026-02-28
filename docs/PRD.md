# Product Requirements Document (PRD)
# US Healthcare Dearth Map

**Version**: 2.0
**Date**: 2026-02-28
**Author**: Karma (for Anand)
**Status**: Implemented — live at [anandpreshob.github.io/healthcare-dearth-map](https://anandpreshob.github.io/healthcare-dearth-map/)

---

## 1. Executive Summary

The **US Healthcare Dearth Map** is an interactive web application that visualizes healthcare access gaps across the United States. It provides granular, data-driven insights into how underserved different geographic areas are for 15 medical specialties, enabling policymakers, healthcare organizations, and researchers to identify where interventions are most needed.

The application is deployed as a **fully static site** on GitHub Pages — no backend server required. All data is pre-computed from NPPES provider records and Census demographics, with OSRM road-network drive times.

---

## 2. Problem Statement

### The Problem
Healthcare access in the United States is highly unequal. Rural areas, low-income urban neighborhoods, and certain regions face severe shortages of healthcare providers. However, there is no comprehensive, publicly accessible tool that:
- Quantifies healthcare access at the county level across all specialties
- Combines provider density with real road-network drive times
- Provides an intuitive visual interface for exploration
- Is freely available without authentication

### Current State
- **HRSA HPSA designations**: Official but coarse-grained, updated infrequently, binary (shortage/no shortage)
- **Academic studies**: Fragmented, focus on single specialties or regions
- **No unified tool**: No interactive map combining density + drive time metrics by specialty across all US counties

### The Solution
A publicly accessible interactive map covering:
- All 3,109 CONUS counties
- 15 medical specialties
- Composite Dearth Score combining provider density (60%) and OSRM drive time (40%)
- County detail with state and national average comparisons
- Search, table view, and CSV export for researchers

---

## 3. Goals and Success Metrics

### Goals
| Goal | Description | Status |
|------|-------------|--------|
| **G1** | Create comprehensive healthcare access dataset at county level | Done |
| **G2** | Build interactive visualization for exploring access gaps | Done |
| **G3** | Enable specialty-specific analysis for all 15 specialties | Done |
| **G4** | Produce publishable research findings | In progress |
| **G5** | Make freely accessible without authentication | Done |

### Success Metrics
| Metric | Target | Actual |
|--------|--------|--------|
| Geographic coverage | 100% of CONUS counties | 3,109 counties (100%) |
| Specialty coverage | 15 specialty categories | 15 specialties |
| Provider data | Real NPPES records | 1,560,696 providers |
| Data freshness | Within last 12 months | Current NPPES data |
| Load time | < 3 seconds for map | ~2-3 seconds |
| Academic output | 1 conference paper | AMIA 2026 submitted |
| Hosting cost | Free | $0 (GitHub Pages) |

---

## 4. Target Users

### Primary Users
1. **Health Policy Researchers**
   - Need: Identify underserved areas for policy recommendations
   - Use case: "Show me counties with worst cardiology access in the Midwest"

2. **Healthcare System Planners**
   - Need: Decide where to build new facilities or expand services
   - Use case: "Where should we open a new dialysis center in Texas?"

3. **Digital Health / AI Companies**
   - Need: Identify markets where AI/telehealth could have most impact
   - Use case: "Which counties have poor mental health access?"

4. **Academic Researchers**
   - Need: Data for healthcare access studies
   - Use case: Export county-level data for statistical analysis

### Secondary Users
- Journalists covering healthcare disparities
- Patients understanding their local options
- Public health students

---

## 5. Features and Requirements

### 5.1 Implemented Features

#### F1: Interactive US Map (P0 — Done)
- Choropleth map of all 3,109 CONUS counties colored by Dearth Score
- Green (well served) → red (severe shortage) color gradient
- Hover to see county name and score via tooltip
- Pan and zoom controls via MapLibre GL JS
- Carto Positron basemap (free, no token required)

#### F2: Specialty Selector (P0 — Done)
- Dropdown with all 15 specialty categories
- Selecting a specialty re-renders map colors from corresponding static JSON file
- Data cached by TanStack React Query for instant re-switching

#### F3: County Detail Panel (P0 — Done)
- Slides in from right when a county is clicked at high zoom
- Shows county name, state, population
- All 15 specialty scores with state and national average comparisons
- Per-specialty provider count, density, drive time, dearth score, and label

#### F4: State Drill-down (P0 — Done)
- Click a state at low zoom → animated `fitBounds()` transition (1200ms) to that state
- At state zoom level, individual counties become clickable
- "Back to US" button for one-click return to national view via `flyTo()` animation

#### F5: Search (P1 — Done)
- Client-side search against pre-loaded index (~1.5 MB, fetched once)
- Counties matched by case-insensitive substring on name or FIPS
- Zip codes matched by prefix
- Results sorted by population, limited to 10
- Debounced input (300ms) with TanStack React Query

#### F6: Data Table View (P1 — Done)
- Full sortable table of all counties for selected specialty
- Columns: county, state, population, dearth score, label, provider count, density
- Export CSV button downloads pre-generated CSV file

#### F7: About / Methodology Page (P1 — Done)
- Explains Dearth Score formula and component weights
- Lists data sources with links
- Describes specialty taxonomy mapping

### 5.2 Future Features (Not Yet Implemented)

#### F8: Zip Code Level Granularity (P2)
- Drill down from county to individual zip codes within a county

#### F9: Appointment Wait Time Integration (P2)
- Add wait time component when reliable data source is obtained

#### F10: Comparison Mode (P3)
- Compare two counties side-by-side

#### F11: Trend Over Time (P3)
- Year-over-year changes using monthly NPPES updates

#### F12: AI/Telehealth Opportunity Score (P2)
- Composite score combining dearth + internet access + demographics

---

## 6. Specialty Categories

| Category | Specialties Included | Example Taxonomy Codes |
|----------|---------------------|------------------------|
| Primary Care | Family Medicine, Internal Medicine, General Practice | 207Q, 207R, 208D |
| Pediatrics | Pediatrics, Pediatric subspecialties | 208000 |
| Cardiology | Cardiovascular Disease, Interventional Cardiology | 207RC |
| Neurology | Neurology, Neurosurgery | 2084N, 207T |
| Nephrology | Nephrology | 207RN |
| Oncology | Medical Oncology, Radiation Oncology | 207RX, 2085R |
| Psychiatry | Psychiatry, Child Psychiatry | 2084P |
| OB/GYN | Obstetrics, Gynecology | 207V |
| Orthopedics | Orthopedic Surgery | 207X |
| General Surgery | General Surgery | 208600 |
| Emergency Medicine | Emergency Medicine | 207P |
| Radiology | Diagnostic Radiology, Interventional Radiology | 2085R |
| Pathology | Anatomic/Clinical Pathology | 207ZP |
| Dermatology | Dermatology | 207N |
| Ophthalmology | Ophthalmology | 207W |

Total: 139 NPI taxonomy codes mapped across 15 categories.

---

## 7. Dearth Score Definition

### Components
The Dearth Score is a composite metric (0-100 scale, higher = more underserved):

| Component | Weight | Description | Data Source |
|-----------|--------|-------------|-------------|
| **Provider Density** | 60% | Providers per 100k population, percentile-ranked | NPPES + Census |
| **Drive Time** | 40% | Minutes to drive to nearest provider via road network | OSRM routing |

### Formula
```
Dearth Score = 0.6 × Density_Score + 0.4 × DriveTime_Score

Where:
- Density_Score  = 100 × (1 - percentile_rank(providers_per_100k))
- DriveTime_Score = 100 × percentile_rank(drive_time_minutes)
```

### Design Decisions
- **Distance removed**: Euclidean distance is strictly subsumed by drive time, which correctly handles road topology (bridges, mountains, etc.)
- **Wait time removed**: No reliable nationwide data source. Placeholder value of 14 days for all counties added no discriminatory power. Can be re-added when real appointment availability data becomes available.
- **60/40 weighting**: Density is weighted higher because a county with one nearby provider serving 200k people is still underserved, even with short drive time.

### Interpretation
| Score Range | Label | Color |
|-------------|-------|-------|
| 0-20 | Well Served | Dark Green |
| 21-40 | Adequate | Light Green |
| 41-60 | Moderate Shortage | Yellow/Orange |
| 61-80 | Significant Shortage | Orange |
| 81-100 | Severe Shortage | Red |

---

## 8. User Stories

### US1: Policy Researcher Explores Map (Done)
> As a **health policy researcher**, I want to **view a national map of healthcare access by specialty** so that I can **identify regions with the worst access gaps for my policy brief**.

Acceptance Criteria:
- [x] Map loads with default specialty (Primary Care)
- [x] I can select different specialties and see map update
- [x] Colors clearly indicate access levels (green → red)
- [x] I can hover over any county to see its score

### US2: Healthcare Planner Investigates a State (Done)
> As a **healthcare system planner**, I want to **explore all counties in Texas for nephrology access** so that I can **decide where to open a new dialysis center**.

Acceptance Criteria:
- [x] I can click Texas to zoom in
- [x] I can select Nephrology specialty
- [x] I can see all Texas counties colored by Nephrology Dearth Score
- [x] I can click a county to see detailed metrics with state/national averages

### US3: Researcher Exports Data (Done)
> As an **academic researcher**, I want to **export Dearth Scores for all counties** so that I can **run my own statistical analysis**.

Acceptance Criteria:
- [x] I can switch to table view
- [x] Table shows all counties sorted by dearth score
- [x] I can export to CSV
- [x] Exported file includes all metrics

### US4: User Searches for Their Location (Done)
> As a **general user**, I want to **search for my county** so that I can **understand how underserved my area is for different specialties**.

Acceptance Criteria:
- [x] Search box accepts county name, FIPS code, or zip code
- [x] Results appear as I type (debounced)
- [x] Clicking a result navigates to that county
- [x] Detail panel shows scores for all 15 specialties with state/national comparisons

---

## 9. Scope

### In Scope (Implemented)
- All 3,109 CONUS counties (48 states + DC)
- 15 medical specialties (139 NPI taxonomy codes)
- 1,560,696 providers from NPPES
- Provider density and OSRM drive time metrics
- Interactive choropleth map with state drill-down
- County detail panel with all specialty scores
- Search (counties by name/FIPS, zip codes by prefix)
- Sortable table view with CSV export
- About/methodology page
- Fully static deployment on GitHub Pages (free, no backend)

### Out of Scope
- US territories (Puerto Rico, Guam, etc.)
- Real-time appointment availability / wait times
- Individual provider listings or contact information
- Patient reviews/ratings
- Insurance network filtering
- Native mobile app (web responsive is in scope)
- Non-English languages
- Sub-county (zip code level) visualization

---

## 10. Technical Constraints

- **Data refresh**: NPPES data updates monthly; current data is a one-time load. Quarterly refresh pipeline can be added.
- **Static site limits**: GitHub Pages has 1 GB size limit. Current static export is ~45 MB, well within bounds.
- **Search**: Client-side only, limited to prefix/substring matching. No fuzzy search or ranking by relevance.
- **Detail bundle**: The `all_counties.json` file (~18 MB) is fetched on first county click. It's cached after first load.

---

## 11. Timeline

| Phase | Deliverables | Status |
|-------|-------------|--------|
| **Phase 1**: Data Foundation | NPPES parsed, Census loaded, PostgreSQL schema | Done |
| **Phase 2**: Core Metrics | Density calculations, basic Dearth Score | Done |
| **Phase 3**: Drive Time | OSRM routing, drive time scores | Done |
| **Phase 4**: Frontend MVP | Interactive map, specialty selector, detail panel | Done |
| **Phase 5**: Polish | Search, table view, export, about page, state drill-down | Done |
| **Phase 6**: Static Deployment | GitHub Pages, no backend required | Done |
| **Phase 7**: Research Paper | AMIA 2026 systems demo submission | In progress |

---

## 12. Risks and Mitigations

| Risk | Status | Resolution |
|------|--------|------------|
| NPI data quality issues | Mitigated | Filtered to active individual providers; validated against HRSA HPSA |
| Drive time computation too slow/expensive | Resolved | Pre-computed via OSRM on remote server (30 cores, 222GB RAM) |
| Appointment wait time data unavailable | Accepted | Launched without; density + drive time provide strong signal |
| Map rendering performance | Resolved | MapLibre GL JS with feature-state coloring; geometry from us-atlas |
| OSRM OOM on local machine | Resolved | Processed on remote Lambda instance; fallback proxy for dev |
| Hosting costs | Resolved | GitHub Pages — free static hosting |

---

## 13. Resolved Questions

| Question | Resolution |
|----------|------------|
| Wait time data source? | Skipped for MVP — no reliable nationwide source. Density + drive time sufficient. |
| Specialty granularity? | 15 categories, 139 taxonomy codes. Covers all major specialties. |
| Public vs. gated? | Fully public, no authentication required. |
| Hosting? | GitHub Pages (free). Static export, no backend needed. |
| Mapping library? | MapLibre GL JS (free, open-source fork of Mapbox GL). No API token required. |
| Branding? | Healthcare Dearth Map |

---

## 14. Appendices

### A. Data Source Links
- NPPES Registry: https://download.cms.gov/nppes/NPI_Files.html
- Census Gazetteer: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
- Census ZCTA-County Crosswalk: https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html
- Geofabrik (road network): https://download.geofabrik.de/north-america.html
- HRSA HPSA Data: https://data.hrsa.gov/topics/health-workforce/shortage-areas
- OSRM: https://project-osrm.org/

### B. Related Work
- HRSA Health Professional Shortage Area (HPSA) Designations
- Dartmouth Atlas of Health Care
- USDA Food Access Research Atlas (methodology reference)

---

*Document ends.*
