# Product Requirements Document (PRD)
# US Healthcare Dearth Map

**Version**: 1.0  
**Date**: 2026-02-06  
**Author**: Karma (for Anand)  
**Status**: Draft

---

## 1. Executive Summary

The **US Healthcare Dearth Map** is an interactive web application that visualizes healthcare access gaps across the United States. It provides granular, data-driven insights into how underserved different geographic areas are for various medical specialties, enabling policymakers, healthcare organizations, and researchers to identify where interventions are most needed.

---

## 2. Problem Statement

### The Problem
Healthcare access in the United States is highly unequal. Rural areas, low-income urban neighborhoods, and certain regions face severe shortages of healthcare providers. However, there is no comprehensive, publicly accessible tool that:
- Quantifies healthcare access at the zip code level
- Breaks down access by medical specialty
- Combines multiple access dimensions (distance, drive time, wait times)
- Provides an intuitive visual interface for exploration

### Current State
- **HRSA HPSA designations**: Official but coarse-grained (county level), updated infrequently, binary (shortage/no shortage)
- **Academic studies**: Fragmented, focus on single specialties or regions
- **No unified tool**: No interactive map combining all access metrics by specialty

### The Opportunity
Build the definitive healthcare access map that:
- Is granular (zip code level)
- Is multi-dimensional (distance + time + wait)
- Is specialty-specific
- Is publicly accessible
- Can inform AI/telehealth investment decisions

---

## 3. Goals and Success Metrics

### Goals
| Goal | Description |
|------|-------------|
| **G1** | Create comprehensive healthcare access dataset at zip-code level |
| **G2** | Build interactive visualization for exploring access gaps |
| **G3** | Enable specialty-specific analysis |
| **G4** | Produce publishable research findings |
| **G5** | Inform where AI/telehealth solutions should be prioritized |

### Success Metrics
| Metric | Target |
|--------|--------|
| Geographic coverage | 100% of US zip codes (41,000+) |
| Specialty coverage | 15+ specialty categories |
| Data freshness | Updated within last 12 months |
| Load time | < 3 seconds for initial map load |
| Academic output | 1 conference paper submission |

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
   - Use case: "Which zip codes have poor mental health access but good internet?"

4. **Academic Researchers**
   - Need: Data for healthcare access studies
   - Use case: Export data for statistical analysis

### Secondary Users
- Journalists covering healthcare
- Patients understanding their local options
- Public health students

---

## 5. Features and Requirements

### 5.1 Core Features (MVP)

#### F1: Interactive US Map
- **Description**: Choropleth map of the United States colored by Dearth Score
- **Requirements**:
  - Display all US counties with color gradient (green = good access, red = poor access)
  - Hover to see county name and Dearth Score
  - Click to zoom into county and see zip-level detail
  - Pan and zoom controls
- **Priority**: P0 (Must Have)

#### F2: Specialty Selector
- **Description**: Dropdown or toggle to select medical specialty
- **Requirements**:
  - At least 15 specialty categories
  - Selecting a specialty re-renders the map with that specialty's Dearth Score
  - Clear visual indication of selected specialty
- **Priority**: P0 (Must Have)

#### F3: County Detail Panel
- **Description**: Side panel showing detailed metrics when a county is selected
- **Requirements**:
  - County name, state, population
  - Dearth Score for selected specialty
  - Component metrics: provider density, average drive time, nearest facility distance
  - Comparison to state and national averages
  - List of all specialties with their Dearth Scores for that county
- **Priority**: P0 (Must Have)

#### F4: Search
- **Description**: Search by zip code, county name, or city
- **Requirements**:
  - Autocomplete suggestions
  - Navigate to and zoom into searched location
  - Display detail panel for searched location
- **Priority**: P1 (Should Have)

#### F5: Data Table View
- **Description**: Tabular view of data for export/analysis
- **Requirements**:
  - Toggle between map and table view
  - Sortable columns (Dearth Score, population, drive time, etc.)
  - Filter by state, Dearth Score range
  - Export to CSV
- **Priority**: P1 (Should Have)

### 5.2 Extended Features (Post-MVP)

#### F6: Zip Code Level Granularity
- **Description**: Drill down from county to individual zip codes
- **Priority**: P2

#### F7: Appointment Wait Time Integration
- **Description**: Add wait time data if partnership/data source obtained
- **Priority**: P2

#### F8: Comparison Mode
- **Description**: Compare two counties or zip codes side-by-side
- **Priority**: P3

#### F9: Trend Over Time
- **Description**: Show how access has changed year-over-year
- **Priority**: P3

#### F10: AI/Telehealth Opportunity Score
- **Description**: Composite score combining dearth + internet access + demographics
- **Priority**: P2

---

## 6. Specialty Categories

| Category | Specialties Included | NPI Taxonomy Prefix |
|----------|---------------------|---------------------|
| Primary Care | Family Medicine, Internal Medicine, General Practice | 207Q, 207R |
| Pediatrics | Pediatrics, Pediatric subspecialties | 208000 |
| Cardiology | Cardiology, Interventional Cardiology | 207RC |
| Neurology | Neurology, Neurosurgery | 2084N, 207T |
| Nephrology | Nephrology | 207RN |
| Oncology | Medical Oncology, Radiation Oncology, Surgical Oncology | 207RX, 2085R |
| Psychiatry | Psychiatry, Child Psychiatry | 2084P |
| OB/GYN | Obstetrics, Gynecology | 207V |
| Orthopedics | Orthopedic Surgery | 207X |
| General Surgery | General Surgery | 208600 |
| Emergency Medicine | Emergency Medicine | 207P |
| Radiology/Diagnostics | Diagnostic Radiology, Interventional Radiology | 2085R |
| Pathology | Pathology | 207ZP |
| Dermatology | Dermatology | 207N |
| Ophthalmology | Ophthalmology | 207W |

---

## 7. Dearth Score Definition

### Components
The Dearth Score is a composite metric (0-100 scale, higher = more underserved):

| Component | Weight | Description | Data Source |
|-----------|--------|-------------|-------------|
| **Provider Density** | 40% | Providers per 100k population | NPI + Census |
| **Distance to Care** | 30% | Average distance to nearest 3 providers (miles) | NPI + geocoding |
| **Drive Time** | 20% | Minutes to drive to nearest provider | OSRM/Google |
| **Wait Time** | 10% | Days to next available appointment | TBD (Phase 2) |

### Formula
```
Raw Score = 0.4 × Density_Score + 0.3 × Distance_Score + 0.2 × DriveTime_Score + 0.1 × WaitTime_Score

Where each component score is normalized:
- Density_Score = 100 × (1 - percentile_rank(density))
- Distance_Score = 100 × percentile_rank(distance)
- DriveTime_Score = 100 × percentile_rank(drive_time)
- WaitTime_Score = 100 × percentile_rank(wait_time) [or 50 if unavailable]

Final Dearth Score = min(100, max(0, Raw Score))
```

### Interpretation
| Score Range | Label | Color |
|-------------|-------|-------|
| 0-20 | Well Served | Dark Green |
| 21-40 | Adequate | Light Green |
| 41-60 | Moderate Shortage | Yellow |
| 61-80 | Significant Shortage | Orange |
| 81-100 | Severe Shortage | Red |

---

## 8. User Stories

### US1: Policy Researcher Explores Map
> As a **health policy researcher**, I want to **view a national map of healthcare access by specialty** so that I can **identify regions with the worst access gaps for my policy brief**.

**Acceptance Criteria**:
- [ ] Map loads with default specialty (Primary Care)
- [ ] I can select different specialties and see map update
- [ ] Colors clearly indicate access levels
- [ ] I can hover over any county to see its score

### US2: Healthcare Planner Investigates a State
> As a **healthcare system planner**, I want to **explore all counties in Texas for nephrology access** so that I can **decide where to open a new dialysis center**.

**Acceptance Criteria**:
- [ ] I can zoom into Texas
- [ ] I can select Nephrology specialty
- [ ] I can see all Texas counties colored by Nephrology Dearth Score
- [ ] I can click a county to see detailed metrics
- [ ] I can compare multiple counties

### US3: Researcher Exports Data
> As an **academic researcher**, I want to **export Dearth Scores for all California zip codes** so that I can **run my own statistical analysis**.

**Acceptance Criteria**:
- [ ] I can switch to table view
- [ ] I can filter by state (California)
- [ ] I can select columns to include
- [ ] I can export to CSV
- [ ] Exported file includes all metrics and methodology notes

### US4: User Searches for Their Location
> As a **general user**, I want to **search for my zip code** so that I can **understand how underserved my area is for different specialties**.

**Acceptance Criteria**:
- [ ] Search box accepts zip code
- [ ] Map zooms to my location
- [ ] Detail panel shows scores for all specialties
- [ ] I can see how my area compares to state average

---

## 9. Scope

### In Scope
- All 50 US states + DC
- ~41,000 zip codes, ~3,100 counties
- 15+ medical specialties
- Provider density, distance, drive time metrics
- Interactive map and table visualization
- CSV export

### Out of Scope (for MVP)
- US territories (Puerto Rico, Guam, etc.)
- Real-time appointment availability
- Individual provider listings
- Patient reviews/ratings
- Insurance network filtering
- Mobile app (web responsive is in scope)
- Non-English languages

---

## 10. Technical Constraints

- **Data refresh**: NPI data updates monthly; plan for quarterly refresh
- **Compute**: Drive time calculations for 41k zip codes × providers is expensive; may need to pre-compute or sample
- **Storage**: Full dataset estimated at 5-10 GB processed
- **API limits**: If using Google Maps, budget for API costs or use OSRM (free)

---

## 11. Timeline

| Phase | Deliverables | Duration | Target Date |
|-------|--------------|----------|-------------|
| **Phase 1**: Data Foundation | NPI parsed, Census data, provider database | 2 weeks | Feb 21, 2026 |
| **Phase 2**: Core Metrics | Density calculations, basic Dearth Score | 1 week | Feb 28, 2026 |
| **Phase 3**: Drive Time | Routing integration, time calculations | 1 week | Mar 7, 2026 |
| **Phase 4**: Frontend MVP | Interactive map, specialty selector, detail panel | 2 weeks | Mar 21, 2026 |
| **Phase 5**: Polish & Launch | Search, table view, export, documentation | 1 week | Mar 28, 2026 |
| **Phase 6**: Research Paper | Write up methodology and findings | 2 weeks | Apr 11, 2026 |

**Total**: ~9 weeks to paper submission (AMIA deadline ~April)

---

## 12. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| NPI data quality issues | Medium | High | Validate against known sources; exclude incomplete records |
| Drive time computation too slow | Medium | Medium | Pre-compute for county centroids only; zip-level on-demand |
| Appointment wait time data unavailable | High | Medium | Launch without; use density as proxy; add later |
| Map rendering performance | Low | Medium | Use vector tiles; aggregate at zoom levels |
| AMIA deadline too tight | Medium | High | Submit to AIiH (April 10) or ML4H as backup |

---

## 13. Open Questions

1. **Wait time data**: Should we pursue Zocdoc partnership, scraping, or skip for MVP?
2. **Specialty granularity**: 15 categories or more? Subspecialties?
3. **Public vs. gated**: Fully public or require account for export?
4. **Hosting**: Where to deploy? (Vercel, AWS, university infrastructure?)
5. **Branding**: Project name? (Healthcare Dearth Map, CareGap, AccessMap?)

---

## 14. Appendices

### A. Data Source Links
- NPI Registry: https://npiregistry.cms.hhs.gov/
- Census ACS: https://www.census.gov/programs-surveys/acs/data.html
- CMS Provider Data: https://data.cms.gov/
- HRSA Data Warehouse: https://data.hrsa.gov/
- OSRM (routing): https://project-osrm.org/

### B. Related Work
- HRSA HPSA Designations
- Dartmouth Atlas of Health Care
- USDA Food Access Research Atlas (methodology reference)

---

*Document ends.*
