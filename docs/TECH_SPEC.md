# Technical Specification
# US Healthcare Dearth Map

**Version**: 2.0
**Date**: 2026-02-28
**Author**: Karma (for Anand)
**Status**: Implemented

---

## 1. System Overview

### 1.1 Architecture Summary

The application uses a **build-time data pipeline** and a **fully static frontend** deployed on GitHub Pages. There is no runtime backend — all data is pre-computed and exported as static JSON/CSV files.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     BUILD-TIME DATA LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ NPPES        │  │ Census       │  │ OpenStreetMap │                  │
│  │ Registry     │  │ Gazetteer +  │  │ Road Network  │                  │
│  │ (1.56M NPI)  │  │ Crosswalk    │  │ (Geofabrik)   │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         └────────────┬────┴────────┬────────┘                           │
│                      ▼             ▼                                    │
│              ┌───────────────────────────────┐                          │
│              │     ETL Pipeline (Python)      │                         │
│              │  - Parse & load raw data       │                         │
│              │  - PostGIS spatial queries     │                         │
│              │  - Map NPI taxonomy → specialty│                         │
│              └───────────────┬───────────────┘                          │
│                              ▼                                          │
│   ┌──────────────────┐   ┌───────────────────────────────┐             │
│   │  OSRM Router     │──►│     PostgreSQL 16 + PostGIS   │             │
│   │  (road-network   │   │  - providers, counties, zctas │             │
│   │   drive times)   │   │  - dearth_scores (46,635)     │             │
│   └──────────────────┘   └───────────────┬───────────────┘             │
│                                          ▼                              │
│                          ┌───────────────────────────────┐             │
│                          │  export_static.py             │             │
│                          │  → JSON + CSV files           │             │
│                          │    (frontend/public/data/)    │             │
│                          └───────────────────────────────┘             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      RUNTIME (GitHub Pages)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│              ┌───────────────────────────────┐                          │
│              │     Next.js 14 Static Export   │                         │
│              │  - MapLibre GL JS choropleth   │                         │
│              │  - TanStack React Query        │                         │
│              │  - Tailwind CSS styling        │                         │
│              └───────────────────────────────┘                          │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │   Map View     │  │  Detail Panel  │  │  Table View    │           │
│  │  - Choropleth  │  │  - All 15 spec │  │  - Sortable    │           │
│  │  - State zoom  │  │  - State avg   │  │  - Export CSV  │           │
│  │  - Click/hover │  │  - Natl avg    │  │  - All counties│           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Database** | PostgreSQL 16 + PostGIS 3.4 | Spatial queries for nearest-provider, KNN; build-time only |
| **ETL** | Python 3.11, psycopg2 | Direct SQL for performance; no pandas/geopandas needed |
| **Routing** | OSRM (self-hosted) | Free, accurate road-network drive times; build-time only |
| **Frontend** | Next.js 14 + React 18 | Static export (`output: "export"`), good DX, ecosystem |
| **Mapping** | MapLibre GL JS | Free, open-source Mapbox GL fork — no token required |
| **Basemap** | Carto Positron | Free vector basemap tiles |
| **Data Fetching** | TanStack React Query | Caching, deduplication, loading states |
| **Styling** | Tailwind CSS | Rapid UI development |
| **Geometry** | us-atlas TopoJSON | Client-side county boundaries merged with score data |
| **Hosting** | GitHub Pages | Free static hosting, automated via GitHub Actions |

---

## 2. Data Sources & Ingestion

### 2.1 NPPES Registry

**Source**: https://download.cms.gov/nppes/NPI_Files.html
**Format**: CSV (monthly full replacement file, ~9.7 GB)
**Records Used**: 1,560,696 active individual providers

**Fields Extracted**:
```
NPI                                    -- Unique provider ID
Entity Type Code                       -- 1=Individual, 2=Organization
Provider Business Practice Location Address
Provider Business Practice Location City
Provider Business Practice Location State
Provider Business Practice Location Postal Code
Healthcare Provider Taxonomy Code 1-15 -- Specialty codes (cols 47, step 4)
NPI Deactivation Date                  -- If deactivated
```

**Processing**:
1. Filter to Entity Type = 1 (individual providers)
2. Filter to active (no deactivation date)
3. Extract all taxonomy codes from columns 47 onwards (step 4)
4. Map taxonomy codes to 15 specialty categories (139 codes total)
5. Use practice location zip code to assign to county via ZCTA-county crosswalk

### 2.2 Census Gazetteer Files

**Source**: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
**Format**: Tab-separated (zipped), 2024 vintage

**Files**:
- County Gazetteer: FIPS, name, state, population, land area, centroid lat/lon
- ZCTA Gazetteer: ZCTA code, state, population, land area, centroid lat/lon

**Note**: TSV files have trailing whitespace in headers — fieldnames must be stripped.

### 2.3 Census ZCTA-County Crosswalk

**Source**: https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html
**Format**: CSV with BOM prefix (requires `utf-8-sig` encoding)
**Purpose**: Maps 33,012 ZCTAs to their primary county FIPS codes

### 2.4 OpenStreetMap Road Network (Geofabrik)

**Source**: https://download.geofabrik.de/north-america.html
**Format**: PBF (Protocol Buffer Format), ~11 GB for US
**Purpose**: Processed with OSRM for road-network drive time computation

### 2.5 HRSA HPSA Designations (Validation)

**Source**: https://data.hrsa.gov/topics/health-workforce/shortage-areas
**Purpose**: Validate Dearth Score against official Health Professional Shortage Area designations

### 2.6 Specialty Taxonomy Mapping

139 NPI taxonomy codes are mapped to 15 specialty categories. The full mapping is in `backend/etl/taxonomy_mapping.py`. Key examples:

```python
SPECIALTY_MAPPING = {
    "primary_care": [
        "207Q00000X",  # Family Medicine
        "207R00000X",  # Internal Medicine
        "208D00000X",  # General Practice
        # + additional subspecialties
    ],
    "cardiology": [
        "207RC0000X",  # Cardiovascular Disease
        "207RI0011X",  # Interventional Cardiology
    ],
    # ... 13 more specialties, 139 codes total
}
```

---

## 3. Database Schema

### 3.1 PostgreSQL + PostGIS Schema

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

-- Specialty categories (lookup table)
CREATE TABLE specialties (
    code VARCHAR(50) PRIMARY KEY,       -- e.g., 'cardiology'
    name VARCHAR(100) NOT NULL          -- e.g., 'Cardiology'
);

-- Geographic units: Counties
CREATE TABLE counties (
    fips VARCHAR(5) PRIMARY KEY,        -- 5-digit FIPS code
    name VARCHAR(100) NOT NULL,
    state_fips VARCHAR(2) NOT NULL,
    state_abbr VARCHAR(2) NOT NULL,
    population INTEGER,
    land_area_sqmi FLOAT,
    centroid GEOMETRY(Point, 4326)
);

CREATE INDEX idx_counties_geom ON counties USING GIST(centroid);
CREATE INDEX idx_counties_state ON counties(state_abbr);

-- Geographic units: Zip codes (ZCTAs)
CREATE TABLE zipcodes (
    zcta VARCHAR(5) PRIMARY KEY,        -- 5-digit ZCTA
    county_fips VARCHAR(5) REFERENCES counties(fips),
    state_abbr VARCHAR(2) NOT NULL,
    population INTEGER,
    land_area_sqmi FLOAT,
    centroid GEOMETRY(Point, 4326)
);

CREATE INDEX idx_zipcodes_geom ON zipcodes USING GIST(centroid);
CREATE INDEX idx_zipcodes_county ON zipcodes(county_fips);

-- Healthcare providers
CREATE TABLE providers (
    npi VARCHAR(10) PRIMARY KEY,
    name VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    location GEOMETRY(Point, 4326),
    specialties VARCHAR(50)[]            -- Our mapped specialty codes
);

CREATE INDEX idx_providers_geom ON providers USING GIST(location);
CREATE INDEX idx_providers_specialties ON providers USING GIN(specialties);

-- Pre-computed dearth scores
CREATE TABLE dearth_scores (
    id SERIAL PRIMARY KEY,
    geo_type VARCHAR(10) NOT NULL,       -- 'county' or 'zipcode'
    geo_id VARCHAR(10) NOT NULL,         -- FIPS or ZCTA
    specialty_code VARCHAR(50) NOT NULL REFERENCES specialties(code),

    -- Component metrics
    provider_count INTEGER,
    provider_density FLOAT,              -- per 100k population
    nearest_distance_miles FLOAT,        -- Euclidean to nearest provider
    avg_distance_top3_miles FLOAT,       -- avg to nearest 3
    drive_time_minutes FLOAT,            -- OSRM road-network drive time
    wait_time_days FLOAT,               -- placeholder (no data source yet)

    -- OSRM fields
    nearest_provider_npi VARCHAR(10),
    nearest_provider_lon FLOAT,
    nearest_provider_lat FLOAT,
    drive_time_is_estimated BOOLEAN DEFAULT FALSE,

    -- Component scores (0-100, higher = worse access)
    density_score FLOAT,
    distance_score FLOAT,
    drivetime_score FLOAT,
    waittime_score FLOAT,

    -- Composite
    dearth_score FLOAT,                  -- 0.6*density + 0.4*drivetime
    dearth_label VARCHAR(25),            -- 'Well Served' .. 'Severe Shortage'

    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_dearth_unique ON dearth_scores(geo_type, geo_id, specialty_code);

-- Materialized view for fast county-level queries
CREATE MATERIALIZED VIEW county_dearth_summary AS
SELECT
    c.fips, c.name, c.state_abbr, c.population,
    s.code AS specialty,
    ds.provider_count, ds.provider_density,
    ds.dearth_score, ds.dearth_label
FROM counties c
CROSS JOIN specialties s
LEFT JOIN dearth_scores ds
    ON ds.geo_type = 'county'
    AND ds.geo_id = c.fips
    AND ds.specialty_code = s.code;

CREATE INDEX idx_county_summary_spec ON county_dearth_summary(specialty);
```

---

## 4. ETL Pipeline

### 4.1 Pipeline Steps

```
download_data         Download NPPES + Census files to SSD (~25 GB)
      │
load_counties         Parse Census Gazetteer → 3,109 counties with centroids
      │
load_zipcodes         Parse ZCTA Gazetteer + crosswalk → 33,012 ZCTAs
      │
load_providers        Parse NPPES CSV (9.7 GB) → 1,560,696 providers
      │
compute_metrics       PostGIS spatial queries → counts, density, nearest provider
      │
compute_drivetimes    OSRM routing → drive times from county centroids
      │
compute_scores        Percentile ranking → 46,635 county-specialty dearth scores
      │
export_static         Export all data as static JSON/CSV → frontend/public/data/
```

### 4.2 ETL Code Structure

```
backend/etl/
├── config.py              # Database URL, weights, OSRM URL, dearth labels
├── taxonomy_mapping.py    # 139 NPI taxonomy codes → 15 specialty categories
├── download_data.py       # Download NPPES + Census files
├── load_counties.py       # Census Gazetteer → counties table
├── load_zipcodes.py       # ZCTA Gazetteer + crosswalk → zipcodes table
├── load_providers.py      # NPPES CSV → providers table
├── compute_metrics.py     # PostGIS KNN queries → provider metrics
├── compute_drivetimes.py  # OSRM routing → drive times
├── compute_scores.py      # Percentile ranking → dearth scores
├── run_pipeline.py        # Orchestrates all steps
├── export_static.py       # Export data as static JSON/CSV files
├── validate_hpsa.py       # Validation against HRSA HPSA designations
└── setup_osrm.sh          # One-time OSRM data preparation
```

### 4.3 Running the Pipeline

```bash
# Full pipeline: download → load → compute → score
python -m backend.etl.run_pipeline

# Skip download (data already on SSD)
python -m backend.etl.run_pipeline --skip-download

# Skip OSRM drive times (uses distance * 2.0 proxy)
python -m backend.etl.run_pipeline --skip-download --skip-drivetimes

# Export static data for GitHub Pages
python -m backend.etl.export_static
```

### 4.4 OSRM Processing

OSRM was processed on a remote Lambda instance (30 cores, 222GB RAM):
- Extract + partition + customize: ~62 minutes
- OSRM Docker image is amd64-only; OOM kills on 16GB Mac even with 1 thread
- Graceful fallback: if OSRM unreachable, keeps proxy values (`distance_miles * 2.0`), sets `drive_time_is_estimated = TRUE`

---

## 5. Static Data Export

### 5.1 Export Script

`backend/etl/export_static.py` queries PostgreSQL and produces all data files the frontend needs:

| File | Description | Size |
|------|-------------|------|
| `specialties.json` | List of 15 specialty codes/names | ~500 B |
| `geojson/counties_{code}.json` (×15) | GeoJSON FeatureCollections (geometry: null) | ~650 KB each |
| `counties/counties_{code}.json` (×15) | County arrays sorted by dearth_score DESC | ~500 KB each |
| `details/all_counties.json` | All counties + all specialties bundled | ~18 MB |
| `search_index.json` | Counties + zipcodes sorted by population | ~1.5 MB |
| `exports/dearth_county_{code}.csv` (×15) | CSV exports matching API route output | ~550 KB each |
| **Total** | | **~45 MB** |

### 5.2 Data Format Examples

**GeoJSON Feature** (geometry is null — frontend merges with us-atlas TopoJSON):
```json
{
  "type": "Feature",
  "geometry": null,
  "properties": {
    "fips": "06001",
    "name": "Alameda County",
    "state": "CA",
    "population": 1682353,
    "dearth_score": 23.4,
    "dearth_label": "Adequate",
    "provider_count": 412,
    "provider_density": 24.5
  }
}
```

**County Detail** (bundled in all_counties.json, keyed by FIPS):
```json
{
  "06001": {
    "fips": "06001",
    "name": "Alameda County",
    "state": "CA",
    "population": 1682353,
    "specialties": [
      {
        "code": "cardiology",
        "name": "Cardiology",
        "provider_count": 42,
        "provider_density": 2.5,
        "dearth_score": 35.2,
        "dearth_label": "Adequate",
        "state_avg_score": 32.1,
        "national_avg_score": 59.99
      }
    ]
  }
}
```

---

## 6. API Design (Build-Time Backend)

The FastAPI backend is used during development and to verify data. In production, all endpoints are replaced by static JSON files.

### 6.1 Endpoints → Static File Mapping

| Original API Endpoint | Static File |
|----------------------|-------------|
| `GET /api/specialties` | `/data/specialties.json` |
| `GET /api/geojson/counties?specialty=X` | `/data/geojson/counties_X.json` |
| `GET /api/counties?specialty=X` | `/data/counties/counties_X.json` |
| `GET /api/counties/{fips}` | `/data/details/all_counties.json` (lookup by FIPS) |
| `GET /api/search?q=X` | `/data/search_index.json` (client-side filter) |
| `GET /api/export?specialty=X` | `/data/exports/dearth_county_X.csv` (direct link) |

### 6.2 Client-Side Search

Search is performed entirely in the browser:
1. On first search, `search_index.json` is fetched and cached in a module-level variable
2. Counties are matched by case-insensitive substring on name or exact match on FIPS
3. Zip codes are matched by prefix
4. Results are sorted by population (descending) and limited to 10

---

## 7. Frontend Design

### 7.1 Component Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with nav bar (Map / Table / About)
│   ├── page.tsx                # Map view — main interactive choropleth
│   ├── table/
│   │   └── page.tsx            # Table view — sortable data table
│   └── about/
│       └── page.tsx            # Methodology and data sources
├── components/
│   ├── Map/
│   │   ├── MapView.tsx         # MapLibre GL JS map, us-atlas TopoJSON
│   │   ├── MapLegend.tsx       # Dearth Score color legend
│   │   └── MapControls.tsx     # Specialty selector + search bar
│   ├── Panels/
│   │   ├── DetailPanel.tsx     # County detail with all 15 specialty scores
│   │   └── SpecialtySelector.tsx
│   └── Table/
│       ├── DataTable.tsx       # Sortable county table
│       └── ExportButton.tsx    # CSV download link
├── hooks/
│   ├── useMapData.ts           # Fetch + merge GeoJSON with TopoJSON geometry
│   ├── useGeoJSON.ts           # Fetch GeoJSON for a specialty
│   ├── useCountyData.ts        # Fetch county list for table view
│   ├── useCountyDetail.ts      # Fetch single county detail (from bundle)
│   ├── useSpecialties.ts       # Fetch specialty list
│   └── useSearch.ts            # Client-side search with debouncing
├── lib/
│   ├── api.ts                  # Static data fetching + client-side search
│   ├── geo.ts                  # us-atlas TopoJSON loading + topojson-client
│   ├── mergeGeoData.ts         # Merge score properties with county geometry
│   ├── colors.ts               # Dearth Score → color interpolation
│   └── constants.ts            # US bounding box, default specialty
├── types/
│   └── index.ts                # TypeScript interfaces
└── public/
    └── data/                   # Pre-exported static JSON/CSV files
```

### 7.2 Key Frontend Patterns

**Geometry/Data Separation**: The frontend loads county boundaries from `us-atlas/counties-10m.json` (TopoJSON) client-side in `lib/geo.ts`. Score data is fetched separately from static JSON files (GeoJSON with `geometry: null`). These are merged in `lib/mergeGeoData.ts` by matching on FIPS code. This allows specialty switching without re-downloading geometry.

**MapLibre GL JS**: The map uses MapLibre GL JS (free, open-source fork of Mapbox GL JS) with Carto Positron basemap tiles. No API token required. County fills are colored using `feature-state` and `fill-color` expressions driven by dearth score data.

**State Drill-down**: At low zoom, clicking a state triggers `map.fitBounds()` with a 1200ms animation to zoom into that state's counties. At high zoom, clicking a county opens the detail panel.

**Client-Side Search**: The search index (~1.5 MB) is fetched once and cached. Searching is instant substring matching on county names/FIPS and prefix matching on zip codes, limited to 10 results sorted by population.

**React Query Caching**: All data fetches use TanStack React Query with appropriate staleTime settings. The search index and county detail bundle use `staleTime: Infinity` since the data is static.

### 7.3 TypeScript Interfaces

```typescript
interface Specialty {
  code: string;        // e.g., "cardiology"
  name: string;        // e.g., "Cardiology"
}

interface CountySummary {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  dearth_score: number | null;
  dearth_label: string | null;
  provider_count: number | null;
  provider_density: number | null;
}

interface SpecialtyScore {
  code: string;
  name: string;
  provider_count: number | null;
  provider_density: number | null;
  nearest_distance_miles: number | null;
  avg_distance_top3_miles: number | null;
  drive_time_minutes: number | null;
  wait_time_days: number | null;
  density_score: number | null;
  distance_score: number | null;
  drivetime_score: number | null;
  waittime_score: number | null;
  dearth_score: number | null;
  dearth_label: string | null;
  state_avg_score: number | null;
  national_avg_score: number | null;
}

interface CountyDetail {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  specialties: SpecialtyScore[];
}

interface SearchResult {
  type: string;        // "county" or "zipcode"
  id: string;          // FIPS or ZCTA
  label: string;       // "Alameda, CA" or "94102 (CA)"
}
```

---

## 8. Dearth Score Formula

### 8.1 Current Formula (v2)

```
Dearth Score = 0.6 × Density Score + 0.4 × Drive Time Score
```

| Component | Weight | Formula | Data Source |
|-----------|--------|---------|-------------|
| **Density Score** | 60% | `100 × (1 - percentile_rank(density))` | NPPES provider count / Census population |
| **Drive Time Score** | 40% | `100 × percentile_rank(drive_time)` | OSRM road-network routing |

### 8.2 Score Labels

| Score Range | Label |
|-------------|-------|
| 0 - 20 | Well Served |
| 21 - 40 | Adequate |
| 41 - 60 | Moderate Shortage |
| 61 - 80 | Significant Shortage |
| 81 - 100 | Severe Shortage |

### 8.3 Design Rationale

**Why only two factors?**
- **Density** captures whether enough providers exist relative to population.
- **Drive time** captures geographic accessibility via real road networks.
- **Euclidean distance** was removed — drive time strictly subsumes it and correctly handles cases where road topology differs from straight-line distance (bridges, mountain passes, etc.).
- **Wait time** was removed — no reliable nationwide data source exists. The placeholder value (14 days for all counties) added no discriminatory power. Can be re-added when real appointment availability data becomes available.

**Why 60/40 weighting?**
- Provider density is the primary determinant of access — a county can have a short drive time to one provider but still be severely underserved if that provider serves 200k people.
- Drive time is secondary but important for rural areas where the nearest specialist may be hours away.

---

## 9. Deployment

### 9.1 GitHub Pages (Production)

The site is deployed as a fully static export on GitHub Pages:

- **URL**: https://anandpreshob.github.io/healthcare-dearth-map/
- **Build**: `next build` with `output: "export"` produces an `out/` directory
- **CI/CD**: GitHub Actions workflow (`.github/workflows/deploy.yml`) triggers on push to `main`
- **Base path**: `/healthcare-dearth-map` (repo name prefix for asset URLs)

### 9.2 Environment Variables

```bash
# Production (GitHub Pages)
NEXT_PUBLIC_BASE_PATH=/healthcare-dearth-map
NEXT_PUBLIC_DATA_BASE=/healthcare-dearth-map/data

# Development (local static data)
NEXT_PUBLIC_BASE_PATH=
NEXT_PUBLIC_DATA_BASE=/data

# Build-time database (ETL only)
DATABASE_URL=postgresql://dearth:dearth_pass@localhost:5432/dearth_map
OSRM_URL=http://localhost:5000
```

### 9.3 GitHub Actions Workflow

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - name: Install and build
        working-directory: frontend
        env:
          NEXT_PUBLIC_BASE_PATH: /healthcare-dearth-map
          NEXT_PUBLIC_DATA_BASE: /healthcare-dearth-map/data
        run: npm ci && npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with: { path: frontend/out }
      - uses: actions/deploy-pages@v4
```

### 9.4 Docker Services (Build-Time Only)

```yaml
# docker-compose.yml
services:
  db:
    image: postgis/postgis:16-3.4
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: dearth_map
      POSTGRES_USER: dearth
      POSTGRES_PASSWORD: dearth_pass
  osrm:
    image: osrm/osrm-backend:latest
    ports: ["5000:5000"]
    # Requires pre-processed road network data
```

---

## 10. Development Phases (Completed)

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1**: Data Foundation | Done | NPPES parsed, Census loaded, PostgreSQL + PostGIS schema |
| **Phase 2**: Core Metrics | Done | Provider density, nearest provider, dearth scores |
| **Phase 3**: Drive Time | Done | OSRM road-network routing for all 46,635 county-specialty pairs |
| **Phase 4**: Frontend MVP | Done | MapLibre choropleth, specialty selector, detail panel, search |
| **Phase 5**: Polish | Done | Table view, CSV export, about page, state drill-down |
| **Phase 6**: Static Export | Done | GitHub Pages deployment, no backend required |
| **Phase 7**: Research Paper | In progress | AMIA 2026 systems demo submission |

---

## 11. Testing & Validation

### Data Validation
- Dearth Scores validated against HRSA HPSA designations (`backend/etl/validate_hpsa.py`)
- Spot-checked known shortage areas (rural TX, MT, NE) against provider directories
- Verified provider counts against published NPPES statistics

### Frontend Verification
- Map loads with primary care choropleth on initial page load
- Specialty selector re-renders map with correct data
- State drill-down zoom animation works at low zoom
- County click opens detail panel with all 15 specialty scores
- Search returns county/zipcode results with correct navigation
- Table view is sortable and CSV export downloads correct file
- All pages (map, table, about) render correctly on GitHub Pages

---

## 12. Future Enhancements

1. **Real-time appointment data** — Partner with Zocdoc, Healthgrades for wait time component
2. **Telehealth overlay** — Show where telehealth could bridge gaps
3. **Trend analysis** — Year-over-year changes with NPPES monthly updates
4. **Demographic filters** — Age, income, insurance status
5. **Zip code drill-down** — Sub-county level visualization
6. **Comparison mode** — Side-by-side county comparison
7. **API for researchers** — Public REST API access
8. **Embedding** — Allow other sites to embed maps via iframe

---

*Document ends.*
