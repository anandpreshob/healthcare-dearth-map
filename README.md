# US Healthcare Dearth Map

Interactive web application that visualizes healthcare access gaps across the United States. It provides granular, data-driven insights into how underserved different geographic areas are for 15 medical specialties, using a composite **Dearth Score** (0-100) derived from real provider data and road-network drive times.

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  PostgreSQL 16   │     │  FastAPI Backend  │     │  Next.js Frontend│
│  + PostGIS 3.4   │◄────│  (Python 3.11)   │◄────│  + MapLibre GL   │
│  (Docker)        │     │  Port 8000       │     │  Port 3000       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        ▲
        │
┌──────────────────┐
│  OSRM Router     │
│  (Port 5000)     │
└──────────────────┘
```

- **Database**: PostgreSQL + PostGIS with pre-computed dearth scores for all 3,109 CONUS counties
- **Backend**: FastAPI serving REST API + GeoJSON endpoints
- **Frontend**: Next.js 14 with MapLibre GL JS choropleth map, TanStack Query, Tailwind CSS
- **ETL**: Python pipeline ingesting real NPPES provider data and Census demographics
- **Routing**: OSRM (Open Source Routing Machine) for road-network drive time computation

## Data Sources

| Source | Description | Size |
|--------|-------------|------|
| [NPPES](https://download.cms.gov/nppes/NPI_Files.html) | National provider registry — 1.56M matched providers | 9.7 GB |
| [Census Gazetteer](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html) | County + ZCTA centroids, populations, land areas | ~10 MB |
| [Census ZCTA-County Crosswalk](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html) | Maps 33,012 ZCTAs to counties | ~5 MB |
| [Geofabrik US PBF](https://download.geofabrik.de/north-america.html) | OpenStreetMap road network for OSRM routing | 11 GB |

## Documentation

- [PRD.md](./docs/PRD.md) - Product Requirements Document
- [TECH_SPEC.md](./docs/TECH_SPEC.md) - Technical Specification

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 20+](https://nodejs.org/) (for frontend development)
- Python 3.11+ with pip
- External SSD or large disk for data files (~25 GB)
- OSRM server (see [OSRM Setup](#osrm-setup) below)

## Quick Start

### 1. Start the database

```bash
docker compose up db -d
```

### 2. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Run the ETL pipeline

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

### 4. Start the backend

```bash
docker compose up backend -d
# or directly:
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Open in browser

- **Map View**: http://localhost:3000
- **Table View**: http://localhost:3000/table
- **About/Methodology**: http://localhost:3000/about

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

## Features

- **Choropleth Map**: All 3,109 CONUS counties colored by Dearth Score (green=well-served, red=severe shortage)
- **15 Specialties**: Primary Care, Cardiology, Neurology, Nephrology, Oncology, Psychiatry, OB/GYN, Orthopedics, General Surgery, Emergency Medicine, Radiology, Pathology, Dermatology, Ophthalmology, Pediatrics
- **County Detail Panel**: Click any county to see per-specialty scores with state comparisons
- **State Drill-down**: Click a state to zoom in and see county-level detail
- **Search**: Find counties and zip codes by name
- **Table View**: Sortable data table with CSV export
- **Methodology Page**: Explains the Dearth Score formula and data sources

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/specialties` | List all 15 specialty categories |
| `GET /api/counties?specialty=X` | Counties with dearth scores for a specialty |
| `GET /api/counties/{fips}` | Detailed county metrics for all specialties |
| `GET /api/zipcodes/{zcta}` | Zip code detail |
| `GET /api/search?q=X` | Search counties and zip codes |
| `GET /api/geojson/counties?specialty=X` | GeoJSON FeatureCollection for map rendering |
| `GET /api/export?specialty=X` | CSV export |

## Dearth Score Formula

```
Dearth Score = 0.6 x Density Score + 0.4 x Drive Time Score
```

| Component | Weight | How Scored |
|-----------|--------|------------|
| Provider Density | 60% | `100 x (1 - percentile_rank)` of providers per 100k population within each specialty |
| Drive Time | 40% | `100 x percentile_rank` of OSRM road-network drive time (minutes) to nearest provider |

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
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Backend | Python 3.11, FastAPI, asyncpg, databases |
| ETL | Python, psycopg2, PostGIS spatial queries |
| Routing | OSRM (Open Source Routing Machine) with MLD algorithm |
| Frontend | Next.js 14, React 18, TypeScript |
| Mapping | MapLibre GL JS (free, open-source) |
| Styling | Tailwind CSS |
| Data Fetching | TanStack React Query |
| Basemap | Carto Positron (free) |

## Project Structure

```
healthcare-dearth-map/
├── docker-compose.yml          # PostgreSQL + backend + OSRM services
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Settings
│   │   ├── database.py         # Async DB connection
│   │   ├── models/schemas.py   # Pydantic models
│   │   └── routes/             # API route handlers
│   ├── db/
│   │   ├── schema.sql          # PostGIS schema + seed specialties
│   │   └── seed.py             # Run ETL pipeline
│   └── etl/
│       ├── config.py           # ETL settings (DB, weights, OSRM URL)
│       ├── taxonomy_mapping.py # 139 NPI taxonomy → 15 specialty mapping
│       ├── download_data.py    # Download NPPES + Census files
│       ├── load_counties.py    # Census Gazetteer → counties table
│       ├── load_zipcodes.py    # ZCTA Gazetteer + crosswalk → zipcodes table
│       ├── load_providers.py   # NPPES CSV → providers table
│       ├── compute_metrics.py  # PostGIS KNN queries → provider metrics
│       ├── compute_drivetimes.py # OSRM routing → drive times
│       ├── compute_scores.py   # Percentile ranking → dearth scores
│       ├── run_pipeline.py     # Pipeline orchestrator
│       └── setup_osrm.sh       # One-time OSRM data preparation
├── frontend/
│   ├── package.json
│   ├── next.config.js          # API proxy to backend
│   ├── app/                    # Next.js pages
│   ├── components/             # React components
│   ├── hooks/                  # TanStack Query hooks
│   ├── lib/                    # Utilities
│   └── types/                  # TypeScript interfaces
└── docs/
    ├── PRD.md                  # Product requirements
    └── TECH_SPEC.md            # Technical specification
```

## Target Publications

- AMIA Annual Symposium 2026
- AIiH 2026
- JAMIA (journal)
