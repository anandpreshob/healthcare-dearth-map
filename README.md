# US Healthcare Dearth Map

Interactive web application that visualizes healthcare access gaps across the United States. It provides granular, data-driven insights into how underserved different geographic areas are for 15 medical specialties, using a composite **Dearth Score** (0-100).

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  PostgreSQL 16   │     │  FastAPI Backend  │     │  Next.js Frontend│
│  + PostGIS 3.4   │◄────│  (Python 3.11)   │◄────│  + MapLibre GL   │
│  (Docker)        │     │  Port 8000       │     │  Port 3000       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

- **Database**: PostgreSQL + PostGIS with pre-computed dearth scores
- **Backend**: FastAPI serving REST API + GeoJSON endpoints
- **Frontend**: Next.js 14 with MapLibre GL JS choropleth map, TanStack Query, Tailwind CSS
- **ETL**: Python pipeline generating sample data for 5 states (~200 counties, ~5000 providers)

## Documentation

- [PRD.md](./docs/PRD.md) - Product Requirements Document
- [TECH_SPEC.md](./docs/TECH_SPEC.md) - Technical Specification

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 20+](https://nodejs.org/) (for frontend development)

## Quick Start

### 1. Start the database and backend

```bash
# Start PostgreSQL + backend (schema.sql runs automatically on first start)
docker-compose up -d
```

### 2. Seed the database with sample data

```bash
# Run the ETL pipeline to generate sample data and compute dearth scores
docker-compose exec backend python -m backend.db.seed
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open in browser

- **Map View**: http://localhost:3000
- **Table View**: http://localhost:3000/table
- **About/Methodology**: http://localhost:3000/about

## Features

- **Choropleth Map**: Counties colored by Dearth Score (green=well-served, red=severe shortage)
- **15 Specialties**: Primary Care, Cardiology, Neurology, Nephrology, Oncology, Psychiatry, OB/GYN, Orthopedics, General Surgery, Emergency Medicine, Radiology, Pathology, Dermatology, Ophthalmology, Pediatrics
- **County Detail Panel**: Click any county to see per-specialty scores with state comparisons
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
Dearth Score = 0.4 x Density Score + 0.3 x Distance Score + 0.2 x DriveTime Score + 0.1 x WaitTime Score
```

| Component | Weight | How Scored |
|-----------|--------|------------|
| Provider Density | 40% | 100 x (1 - percentile rank of providers per 100k) |
| Distance to Care | 30% | 100 x percentile rank of distance to nearest providers |
| Drive Time | 20% | Approximated as 1.5x distance (MVP) |
| Wait Time | 10% | Default score of 50 (pending real data) |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Backend | Python 3.11, FastAPI, asyncpg, databases |
| ETL | Python, psycopg2, PostGIS spatial queries |
| Frontend | Next.js 14, React 18, TypeScript |
| Mapping | MapLibre GL JS (free, open-source) |
| Styling | Tailwind CSS |
| Data Fetching | TanStack React Query |
| Basemap | Carto Positron (free) |

## Project Structure

```
healthcare-dearth-map/
├── docker-compose.yml          # PostgreSQL + backend services
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
│       ├── config.py           # ETL settings
│       ├── taxonomy_mapping.py # NPI specialty mapping
│       ├── generate_sample_data.py  # Sample data for 5 states
│       ├── compute_metrics.py  # Provider metrics via PostGIS
│       ├── compute_scores.py   # Dearth score calculation
│       └── run_pipeline.py     # Pipeline orchestrator
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

## Sample Data

The ETL pipeline generates realistic sample data for 5 states with deliberate dearth patterns:

| State | Counties | Pattern |
|-------|----------|---------|
| California | 40 | Urban counties well-served, rural moderate |
| Texas | 45 | Major metros well-served, west TX shortage |
| New York | 40 | NYC area well-served, upstate moderate |
| Mississippi | 40 | Mostly underserved, Delta region severe |
| Montana | 40 | Very few providers, most counties in shortage |

## Target Publications

- AMIA Annual Symposium 2026
- AIiH 2026
- JAMIA (journal)
