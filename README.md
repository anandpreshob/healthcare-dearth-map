# US Healthcare Dearth Map

Interactive web application that visualizes healthcare access gaps across the United States. It provides granular, data-driven insights into how underserved different geographic areas are for 15 medical specialties, using a composite **Dearth Score** (0-100) derived from real provider data and road-network drive times.

**Live Site**: [https://anandpreshob.github.io/healthcare-dearth-map/](https://anandpreshob.github.io/healthcare-dearth-map/)

## Architecture

The application is deployed as a **fully static site** on GitHub Pages. All data is pre-computed and exported as static JSON/CSV files — no backend server required at runtime.

```
BUILD TIME (one-time data pipeline):
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  PostgreSQL 16   │     │  ETL Pipeline    │     │  OSRM Router     │
│  + PostGIS 3.4   │◄────│  (Python 3.11)   │────►│  (Port 5000)     │
│  (Docker)        │     │                  │     │  Road-network    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │  export_static.py    │
                    │  JSON + CSV files    │
                    └──────────────────────┘

RUNTIME (GitHub Pages):
┌──────────────────────────────────────────────────────────────────┐
│  Browser                                                         │
│  ┌────────────────────┐     ┌──────────────────────────────┐    │
│  │  Next.js Static    │────►│  Static JSON/CSV files       │    │
│  │  + MapLibre GL JS  │     │  (specialties, geojson,      │    │
│  │  + TanStack Query  │     │   counties, details, search) │    │
│  └────────────────────┘     └──────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

- **Database**: PostgreSQL + PostGIS with pre-computed dearth scores for all 3,109 CONUS counties (build-time only)
- **ETL**: Python pipeline ingesting real NPPES provider data and Census demographics
- **Routing**: OSRM (Open Source Routing Machine) for road-network drive time computation (build-time only)
- **Frontend**: Next.js 14 static export with MapLibre GL JS choropleth map, TanStack Query, Tailwind CSS
- **Hosting**: GitHub Pages — automated deploy via GitHub Actions on push to `main`

## Data Sources

| Source | Description | Size |
|--------|-------------|------|
| [NPPES](https://download.cms.gov/nppes/NPI_Files.html) | National provider registry — 1.56M matched providers | 9.7 GB |
| [Census Gazetteer](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html) | County + ZCTA centroids, populations, land areas | ~10 MB |
| [Census ZCTA-County Crosswalk](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html) | Maps 33,012 ZCTAs to counties | ~5 MB |
| [Geofabrik US PBF](https://download.geofabrik.de/north-america.html) | OpenStreetMap road network for OSRM routing | 11 GB |

## Documentation

- [PRD.md](./docs/PRD.md) — Product Requirements Document
- [TECH_SPEC.md](./docs/TECH_SPEC.md) — Technical Specification
- [STATIC_SITE_IMPLEMENTATION.md](./STATIC_SITE_IMPLEMENTATION.md) — Static site conversion plan

## Features

- **Choropleth Map**: All 3,109 CONUS counties colored by Dearth Score (green = well-served, red = severe shortage)
- **15 Specialties**: Primary Care, Cardiology, Neurology, Nephrology, Oncology, Psychiatry, OB/GYN, Orthopedics, General Surgery, Emergency Medicine, Radiology, Pathology, Dermatology, Ophthalmology, Pediatrics
- **County Detail Panel**: Click any county to see per-specialty scores with state and national comparisons
- **State Drill-down**: Click a state at low zoom to zoom in with animated transition and see county-level detail
- **Search**: Client-side search for counties (by name or FIPS) and zip codes (by prefix), sorted by population
- **Table View**: Sortable data table of all counties with CSV export
- **Methodology Page**: Explains the Dearth Score formula and data sources
- **Back to US**: One-click flyTo animation to return to national view

## Dearth Score Formula

```
Dearth Score = 0.6 × Density Score + 0.4 × Drive Time Score
```

| Component | Weight | How Scored |
|-----------|--------|------------|
| Provider Density | 60% | `100 × (1 - percentile_rank)` of providers per 100k population within each specialty |
| Drive Time | 40% | `100 × percentile_rank` of OSRM road-network drive time (minutes) to nearest provider |

Higher score = worse access. Labels:

| Score Range | Label |
|-------------|-------|
| 0 - 20 | Well Served |
| 21 - 40 | Adequate |
| 41 - 60 | Moderate Shortage |
| 61 - 80 | Significant Shortage |
| 81 - 100 | Severe Shortage |

### Why these two factors?

- **Density** captures whether enough providers exist relative to population — a county with 2 cardiologists for 500k people is underserved even if one is nearby.
- **Drive time** captures geographic accessibility via real road networks — a provider 5 miles away as the crow flies may be a 45-minute drive through mountain roads.
- **Euclidean distance** was removed because drive time strictly subsumes it and handles cases where road topology differs significantly from straight-line distance (bridges, mountain passes, etc.).
- **Wait time** was removed because no reliable nationwide data source exists. It can be added when real appointment availability data becomes available.

## Quick Start

### View the live site

Visit [https://anandpreshob.github.io/healthcare-dearth-map/](https://anandpreshob.github.io/healthcare-dearth-map/) — no setup needed.

### Rebuild from source

To regenerate the data and rebuild the static site:

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 20+](https://nodejs.org/)
- Python 3.11+ with pip
- External SSD or large disk for raw data files (~25 GB)
- OSRM server (optional — see [OSRM Setup](#osrm-setup) below)

#### 1. Start the database

```bash
docker compose up db -d
```

#### 2. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

#### 3. Run the ETL pipeline

```bash
# Full pipeline: downloads data, computes metrics, queries OSRM, calculates scores
python -m backend.etl.run_pipeline

# Skip download if data files already exist on SSD
python -m backend.etl.run_pipeline --skip-download

# Skip OSRM drive times (uses distance proxy instead)
python -m backend.etl.run_pipeline --skip-download --skip-drivetimes
```

The pipeline takes ~5 minutes (with OSRM available) and processes:
- 3,109 CONUS counties
- 33,012 ZCTAs (zip code tabulation areas)
- 1,560,696 providers across 139 taxonomy codes mapped to 15 specialties
- 46,635 county-specialty dearth scores

#### 4. Export static data

```bash
python -m backend.etl.export_static
```

This exports all API data as static JSON/CSV files to `frontend/public/data/`:

```
frontend/public/data/
├── specialties.json                     # All 15 specialties
├── geojson/counties_{code}.json (×15)   # GeoJSON FeatureCollections for map
├── counties/counties_{code}.json (×15)  # County arrays for table view
├── details/all_counties.json            # Bundled detail for all counties
├── search_index.json                    # Counties + zip codes for search
└── exports/dearth_county_{code}.csv (×15) # CSV exports
```

Total: ~45 MB uncompressed.

#### 5. Build and preview the static site

```bash
cd frontend
npm install
npm run build      # produces out/ directory
npx serve out      # preview at http://localhost:3000
```

#### 6. Deploy to GitHub Pages

Deployment is automated via GitHub Actions. Push to `main` and the workflow at `.github/workflows/deploy.yml` will build and deploy to GitHub Pages.

To deploy manually:
```bash
npx gh-pages -d frontend/out
```

## OSRM Setup

OSRM provides real road-network drive times from county centroids to nearest providers. Processing the US road network requires significant RAM (16GB+ for extract), so a remote server is recommended.

### Option A: Remote server (recommended for processing)

On a machine with 32GB+ RAM:

```bash
# Install osmium and Docker, then:
mkdir -p /tmp/osrm
wget -O /tmp/osrm/us-latest.osm.pbf https://download.geofabrik.de/north-america/us-latest.osm.pbf
osmium tags-filter /tmp/osrm/us-latest.osm.pbf w/highway -o /tmp/osrm/us-roads.osm.pbf

docker run --rm -v /tmp/osrm:/data osrm/osrm-backend:latest \
  osrm-extract -t $(nproc) -p /opt/car.lua /data/us-roads.osm.pbf

docker run --rm -v /tmp/osrm:/data osrm/osrm-backend:latest \
  osrm-partition -t $(nproc) /data/us-roads.osrm

docker run --rm -v /tmp/osrm:/data osrm/osrm-backend:latest \
  osrm-customize -t $(nproc) /data/us-roads.osrm

# Start the routing server
docker run -d -p 5000:5000 -v /tmp/osrm:/data osrm/osrm-backend:latest \
  osrm-routed --algorithm mld /data/us-roads.osrm
```

To access from your local machine via SSH tunnel:
```bash
ssh -f -N -L 5000:localhost:5000 user@remote-server
```

### Option B: Local (macOS with brew)

```bash
brew install osrm-backend osmium-tool
bash backend/etl/setup_osrm.sh
```

Note: `osrm-extract` on the full US road network requires ~6GB RAM and may OOM on 16GB Macs. Use `--skip-drivetimes` to fall back to distance-based proxy.

## ETL Pipeline

```
download_data          Download NPPES + Census files to SSD
      │
load_counties          Parse Census Gazetteer → 3,109 counties with centroids + populations
      │
load_zipcodes          Parse ZCTA Gazetteer + crosswalk → 33,012 ZCTAs mapped to counties
      │
load_providers         Parse NPPES CSV (9.7 GB) → 1,560,696 providers with specialties + locations
      │
compute_metrics        PostGIS spatial queries → provider counts, density, nearest provider per county
      │
compute_drivetimes     OSRM routing → real drive times from county centroids to nearest providers
      │
compute_scores         Percentile ranking → dearth scores and labels for 46,635 county-specialty pairs
      │
export_static          Export all API data as static JSON/CSV files for GitHub Pages
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 16 + PostGIS 3.4 (build-time only) |
| ETL | Python 3.11, psycopg2, PostGIS spatial queries |
| Routing | OSRM (Open Source Routing Machine) with MLD algorithm (build-time only) |
| Frontend | Next.js 14 (static export), React 18, TypeScript |
| Mapping | MapLibre GL JS (free, open-source) |
| Styling | Tailwind CSS |
| Data Fetching | TanStack React Query |
| Basemap | Carto Positron (free) |
| Hosting | GitHub Pages |
| CI/CD | GitHub Actions |

## Project Structure

```
healthcare-dearth-map/
├── .github/workflows/
│   └── deploy.yml                 # GitHub Actions: build + deploy to Pages
├── docker-compose.yml             # PostgreSQL + OSRM services (build-time)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/                       # FastAPI application (build-time only)
│   │   ├── main.py                # App entry point
│   │   ├── config.py              # Settings
│   │   ├── database.py            # Async DB connection
│   │   ├── models/schemas.py      # Pydantic models
│   │   └── routes/                # API route handlers
│   ├── db/
│   │   └── schema.sql             # PostGIS schema + seed specialties
│   └── etl/
│       ├── config.py              # ETL settings (DB, weights, OSRM URL)
│       ├── taxonomy_mapping.py    # 139 NPI taxonomy → 15 specialty mapping
│       ├── download_data.py       # Download NPPES + Census files
│       ├── load_counties.py       # Census Gazetteer → counties table
│       ├── load_zipcodes.py       # ZCTA Gazetteer + crosswalk → zipcodes table
│       ├── load_providers.py      # NPPES CSV → providers table
│       ├── compute_metrics.py     # PostGIS KNN queries → provider metrics
│       ├── compute_drivetimes.py  # OSRM routing → drive times
│       ├── compute_scores.py      # Percentile ranking → dearth scores
│       ├── run_pipeline.py        # Pipeline orchestrator
│       ├── export_static.py       # Export all data as static JSON/CSV
│       ├── validate_hpsa.py       # Validation against HRSA HPSA designations
│       └── setup_osrm.sh          # One-time OSRM data preparation
├── frontend/
│   ├── package.json
│   ├── next.config.js             # Static export config
│   ├── .env.production            # GitHub Pages base path
│   ├── .env.development           # Local dev base path
│   ├── app/                       # Next.js pages (map, table, about)
│   ├── components/                # React components
│   ├── hooks/                     # TanStack Query hooks
│   ├── lib/
│   │   ├── api.ts                 # Static data fetching + client-side search
│   │   ├── geo.ts                 # us-atlas TopoJSON loading
│   │   ├── mergeGeoData.ts        # Merge score data with geometry
│   │   ├── colors.ts              # Color scale functions
│   │   └── constants.ts           # US bounds and defaults
│   ├── types/                     # TypeScript interfaces
│   └── public/data/               # Pre-exported static data files
└── docs/
    ├── PRD.md                     # Product requirements
    └── TECH_SPEC.md               # Technical specification
```

## Static Data Files

The frontend serves pre-exported data files from `frontend/public/data/`. These are generated by `python -m backend.etl.export_static` and committed to the repository.

| File Pattern | Count | Description |
|-------------|-------|-------------|
| `specialties.json` | 1 | All 15 specialty codes and names |
| `geojson/counties_{code}.json` | 15 | GeoJSON FeatureCollections (geometry: null, properties only) |
| `counties/counties_{code}.json` | 15 | County arrays sorted by dearth_score DESC (for table view) |
| `details/all_counties.json` | 1 | All counties bundled with per-specialty scores + state/national averages |
| `search_index.json` | 1 | Counties + zip codes sorted by population (for client-side search) |
| `exports/dearth_county_{code}.csv` | 15 | Pre-generated CSV exports |

## Disclaimer

**This tool is for research and educational purposes only.** It is not a substitute for professional medical advice, diagnosis, or treatment. The Dearth Scores and visualizations are derived from publicly available datasets and computational models that may not reflect current real-world conditions. Users should not make healthcare, policy, or business decisions based solely on this tool without independent verification.

## License

This project is licensed under the [MIT License](./LICENSE). You are free to use, modify, and distribute the code and data with attribution. The software is provided "as is", without warranty of any kind.

## Target Publications

- AMIA Annual Symposium 2026
- AIiH 2026
- JAMIA (journal)
