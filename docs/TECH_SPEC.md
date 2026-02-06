# Technical Specification
# US Healthcare Dearth Map

**Version**: 1.0  
**Date**: 2026-02-06  
**Author**: Karma (for Anand)  
**Status**: Draft

---

## 1. System Overview

### 1.1 Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ NPI Registry │  │ Census ACS   │  │ CMS Provider │  │ HRSA HPSA    │ │
│  │ (7M+ records)│  │ (Population) │  │ (Hospitals)  │  │ (Validation) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │                 │          │
│         └────────────┬────┴────────┬────────┴─────────────────┘          │
│                      ▼             ▼                                     │
│              ┌───────────────────────────────┐                           │
│              │     ETL Pipeline (Python)      │                          │
│              │  - Parse & clean raw data      │                          │
│              │  - Geocode addresses           │                          │
│              │  - Map NPI taxonomy → specialty│                          │
│              └───────────────┬───────────────┘                           │
│                              ▼                                           │
│              ┌───────────────────────────────┐                           │
│              │     PostgreSQL + PostGIS       │                          │
│              │  - providers table             │                          │
│              │  - zip_codes table             │                          │
│              │  - counties table              │                          │
│              │  - dearth_scores table         │                          │
│              └───────────────┬───────────────┘                           │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                           API LAYER                                      │
├──────────────────────────────┼───────────────────────────────────────────┤
│                              ▼                                           │
│              ┌───────────────────────────────┐                           │
│              │     FastAPI Backend            │                          │
│              │  GET /api/counties             │                          │
│              │  GET /api/counties/{fips}      │                          │
│              │  GET /api/zipcodes/{zip}       │                          │
│              │  GET /api/specialties          │                          │
│              │  GET /api/scores?geo=&spec=    │                          │
│              │  GET /api/export               │                          │
│              └───────────────┬───────────────┘                           │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                        FRONTEND LAYER                                    │
├──────────────────────────────┼───────────────────────────────────────────┤
│                              ▼                                           │
│              ┌───────────────────────────────┐                           │
│              │     Next.js + React            │                          │
│              │  - MapboxGL for mapping        │                          │
│              │  - TanStack Query for data     │                          │
│              │  - Tailwind CSS styling        │                          │
│              └───────────────────────────────┘                           │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │   Map View     │  │  Detail Panel  │  │  Table View    │             │
│  │  - Choropleth  │  │  - Metrics     │  │  - Sortable    │             │
│  │  - Zoom/pan    │  │  - Comparison  │  │  - Filterable  │             │
│  │  - Click       │  │  - All specs   │  │  - Export CSV  │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Database** | PostgreSQL 16 + PostGIS | Spatial queries, mature, scalable |
| **Backend** | Python 3.11 + FastAPI | Fast development, good data science libraries |
| **ETL** | Python (pandas, geopandas) | Data wrangling |
| **Routing** | OSRM (self-hosted) or Google Maps API | Drive time calculations |
| **Frontend** | Next.js 14 + React 18 | SSR, good DX, ecosystem |
| **Mapping** | Mapbox GL JS | Best-in-class vector maps |
| **Styling** | Tailwind CSS | Rapid UI development |
| **Hosting** | Vercel (frontend) + Railway/Render (backend) | Easy deployment |
| **Data Storage** | S3 or GCS | Raw data files |

---

## 2. Data Sources & Ingestion

### 2.1 NPI Registry

**Source**: https://download.cms.gov/nppes/NPI_Files.html  
**Format**: CSV (monthly full replacement file, ~8GB compressed)  
**Update Frequency**: Monthly  
**Records**: ~7.5 million providers

**Fields to Extract**:
```
NPI                         -- Unique provider ID
Entity Type Code            -- 1=Individual, 2=Organization
Provider Business Practice Location Address
Provider Business Practice Location City
Provider Business Practice Location State
Provider Business Practice Location Postal Code
Healthcare Provider Taxonomy Code 1-15  -- Specialty codes
Provider Enumeration Date   -- When registered
NPI Deactivation Date       -- If deactivated
```

**Processing**:
1. Filter to Entity Type = 1 (individual providers) for density
2. Filter to active (no deactivation date)
3. Map taxonomy codes to specialty categories (see Section 2.5)
4. Geocode addresses to lat/lon (use Census geocoder or Nominatim)
5. Assign to zip code and county FIPS

### 2.2 Census American Community Survey (ACS)

**Source**: https://api.census.gov/data/2023/acs/acs5  
**Format**: API (JSON)  
**Tables Needed**:
- B01003: Total Population
- S0101: Age and Sex (for demographic weighting if needed)

**Geographic Levels**:
- ZCTA (Zip Code Tabulation Area) - closest to zip codes
- County

**Processing**:
1. Query population for all ZCTAs and counties
2. Store in database with geographic identifiers

### 2.3 CMS Hospital Compare

**Source**: https://data.cms.gov/provider-data/  
**Format**: CSV  
**Datasets**:
- Hospital General Information
- Dialysis Facility Compare
- Nursing Home Compare (if relevant)

**Processing**:
1. Extract facility locations
2. Geocode if needed
3. Tag by specialty/service type

### 2.4 HRSA Data (Validation)

**Source**: https://data.hrsa.gov/topics/health-workforce/shortage-areas  
**Format**: CSV/Shapefile  
**Purpose**: Validate our Dearth Score against official HPSA designations

**Datasets**:
- Health Professional Shortage Areas (HPSA)
- Medically Underserved Areas (MUA)

### 2.5 Specialty Taxonomy Mapping

NPI uses NUCC Healthcare Provider Taxonomy codes. We map to our categories:

```python
SPECIALTY_MAPPING = {
    "primary_care": [
        "207Q00000X",  # Family Medicine
        "207R00000X",  # Internal Medicine
        "208D00000X",  # General Practice
    ],
    "cardiology": [
        "207RC0000X",  # Cardiovascular Disease
        "207RI0011X",  # Interventional Cardiology
    ],
    "neurology": [
        "2084N0400X",  # Neurology
        "207T00000X",  # Neurological Surgery
    ],
    "nephrology": [
        "207RN0300X",  # Nephrology
    ],
    "oncology": [
        "207RX0202X",  # Medical Oncology
        "2085R0001X",  # Radiation Oncology
    ],
    "psychiatry": [
        "2084P0800X",  # Psychiatry
        "2084P0804X",  # Child & Adolescent Psychiatry
    ],
    "obgyn": [
        "207V00000X",  # Obstetrics & Gynecology
    ],
    "orthopedics": [
        "207X00000X",  # Orthopaedic Surgery
    ],
    "general_surgery": [
        "208600000X",  # Surgery
    ],
    "emergency": [
        "207P00000X",  # Emergency Medicine
    ],
    "radiology": [
        "2085R0202X",  # Diagnostic Radiology
        "2085R0205X",  # Interventional Radiology
    ],
    "pathology": [
        "207ZP0101X",  # Anatomic Pathology
        "207ZP0102X",  # Clinical Pathology
    ],
    "dermatology": [
        "207N00000X",  # Dermatology
    ],
    "ophthalmology": [
        "207W00000X",  # Ophthalmology
    ],
    "pediatrics": [
        "208000000X",  # Pediatrics
    ],
}
```

---

## 3. Database Schema

### 3.1 PostgreSQL + PostGIS Schema

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Specialty categories (lookup table)
CREATE TABLE specialties (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- e.g., 'cardiology'
    name VARCHAR(100) NOT NULL,            -- e.g., 'Cardiology'
    description TEXT,
    taxonomy_codes TEXT[]                   -- Array of NPI taxonomy codes
);

-- Geographic units: Counties
CREATE TABLE counties (
    fips VARCHAR(5) PRIMARY KEY,           -- 5-digit FIPS code
    name VARCHAR(100) NOT NULL,
    state_fips VARCHAR(2) NOT NULL,
    state_abbr VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    population INTEGER,
    land_area_sqmi FLOAT,
    centroid GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326)
);

CREATE INDEX idx_counties_geom ON counties USING GIST(boundary);
CREATE INDEX idx_counties_state ON counties(state_abbr);

-- Geographic units: Zip codes (ZCTAs)
CREATE TABLE zipcodes (
    zcta VARCHAR(5) PRIMARY KEY,           -- 5-digit ZCTA
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
    entity_type INTEGER,                   -- 1=Individual, 2=Organization
    name VARCHAR(200),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    location GEOMETRY(Point, 4326),
    taxonomy_codes TEXT[],
    specialties VARCHAR(50)[],             -- Our mapped specialty codes
    enumeration_date DATE,
    last_updated DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_providers_geom ON providers USING GIST(location);
CREATE INDEX idx_providers_state ON providers(state);
CREATE INDEX idx_providers_zip ON providers(zipcode);
CREATE INDEX idx_providers_specialties ON providers USING GIN(specialties);

-- Pre-computed dearth scores
CREATE TABLE dearth_scores (
    id SERIAL PRIMARY KEY,
    geo_type VARCHAR(10) NOT NULL,         -- 'county' or 'zipcode'
    geo_id VARCHAR(10) NOT NULL,           -- FIPS or ZCTA
    specialty_code VARCHAR(50) NOT NULL REFERENCES specialties(code),
    
    -- Component metrics
    provider_count INTEGER,
    provider_density FLOAT,                -- per 100k population
    nearest_distance_miles FLOAT,          -- to nearest provider
    avg_distance_top3_miles FLOAT,         -- avg to nearest 3
    drive_time_minutes FLOAT,              -- to nearest provider
    wait_time_days FLOAT,                  -- if available
    
    -- Scores (0-100, higher = worse access)
    density_score FLOAT,
    distance_score FLOAT,
    drivetime_score FLOAT,
    waittime_score FLOAT,
    
    -- Composite
    dearth_score FLOAT,
    dearth_label VARCHAR(20),              -- 'Well Served', 'Severe Shortage', etc.
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT NOW(),
    data_version VARCHAR(20)
);

CREATE UNIQUE INDEX idx_dearth_unique ON dearth_scores(geo_type, geo_id, specialty_code);
CREATE INDEX idx_dearth_specialty ON dearth_scores(specialty_code);
CREATE INDEX idx_dearth_score ON dearth_scores(dearth_score DESC);

-- Materialized view for fast county-level queries
CREATE MATERIALIZED VIEW county_dearth_summary AS
SELECT 
    c.fips,
    c.name,
    c.state_abbr,
    c.population,
    s.code as specialty,
    ds.provider_count,
    ds.provider_density,
    ds.dearth_score,
    ds.dearth_label,
    c.boundary
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
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Download Raw Data                                      │
│  - NPI full file from CMS (~8GB)                               │
│  - Census ACS population data                                   │
│  - County/ZCTA shapefiles from Census TIGER                    │
│  Output: raw/ directory with source files                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Parse NPI Data                                         │
│  - Filter to individual providers (Entity Type = 1)            │
│  - Filter to active (no deactivation date)                     │
│  - Extract location fields                                      │
│  - Map taxonomy codes to specialty categories                   │
│  Output: providers.parquet (~500MB)                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Geocode Providers                                      │
│  - Batch geocode addresses to lat/lon                          │
│  - Use Census Geocoder (free) or Nominatim                     │
│  - Cache results to avoid re-geocoding                         │
│  Output: providers_geocoded.parquet                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Load Geographic Data                                   │
│  - Import county boundaries and attributes                      │
│  - Import ZCTA boundaries and attributes                        │
│  - Join population data from Census                             │
│  Output: counties, zipcodes tables populated                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Compute Provider Metrics                               │
│  For each (county, specialty):                                  │
│    - Count providers                                            │
│    - Calculate provider density (per 100k pop)                  │
│  For each (zipcode, specialty):                                 │
│    - Find nearest provider (distance in miles)                  │
│    - Calculate avg distance to nearest 3                        │
│  Output: metrics tables updated                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Compute Drive Times (Optional/Phase 2)                 │
│  - For each zip centroid, route to nearest provider            │
│  - Use OSRM or Google Maps API                                  │
│  - Batch process to manage API limits                          │
│  Output: drive_time column populated                            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 7: Calculate Dearth Scores                                │
│  - Compute percentile ranks for each metric                    │
│  - Apply weights and formula                                    │
│  - Assign labels based on score ranges                          │
│  Output: dearth_scores table fully populated                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 8: Refresh Materialized Views                             │
│  - REFRESH MATERIALIZED VIEW county_dearth_summary              │
│  - Generate GeoJSON for frontend                                │
│  Output: Ready for API queries                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 ETL Code Structure

```
etl/
├── __init__.py
├── config.py               # Database URLs, paths, settings
├── download.py             # Step 1: Download raw files
├── parse_npi.py            # Step 2: Parse NPI data
├── geocode.py              # Step 3: Geocode providers
├── load_geography.py       # Step 4: Load counties/zipcodes
├── compute_metrics.py      # Step 5: Provider counts, distances
├── compute_drivetime.py    # Step 6: Routing calculations
├── compute_scores.py       # Step 7: Dearth score calculation
├── refresh_views.py        # Step 8: Materialized views
├── run_pipeline.py         # Orchestrates all steps
└── taxonomy_mapping.py     # Specialty code mappings
```

---

## 5. API Design

### 5.1 Endpoints

#### GET /api/specialties
List all specialty categories.

**Response**:
```json
{
  "specialties": [
    {"code": "primary_care", "name": "Primary Care"},
    {"code": "cardiology", "name": "Cardiology"},
    ...
  ]
}
```

#### GET /api/counties
Get all counties with dearth scores for a specialty.

**Query Parameters**:
- `specialty` (required): Specialty code
- `state` (optional): Filter by state abbreviation
- `min_score` / `max_score` (optional): Filter by dearth score range

**Response**:
```json
{
  "specialty": "cardiology",
  "count": 3143,
  "counties": [
    {
      "fips": "06001",
      "name": "Alameda",
      "state": "CA",
      "population": 1682353,
      "dearth_score": 23.4,
      "dearth_label": "Adequate",
      "provider_count": 412,
      "provider_density": 24.5
    },
    ...
  ]
}
```

#### GET /api/counties/{fips}
Get detailed metrics for a specific county.

**Response**:
```json
{
  "fips": "06001",
  "name": "Alameda County",
  "state": "California",
  "population": 1682353,
  "specialties": [
    {
      "code": "primary_care",
      "name": "Primary Care",
      "provider_count": 1245,
      "provider_density": 74.0,
      "nearest_distance_miles": 2.3,
      "drive_time_minutes": 8,
      "dearth_score": 15.2,
      "dearth_label": "Well Served",
      "state_avg_score": 32.1,
      "national_avg_score": 45.3
    },
    ...
  ]
}
```

#### GET /api/zipcodes/{zcta}
Get detailed metrics for a specific zip code.

**Response**: Similar to county endpoint.

#### GET /api/search
Search for locations.

**Query Parameters**:
- `q`: Search query (zip code, county name, city)

**Response**:
```json
{
  "results": [
    {"type": "zipcode", "id": "94102", "label": "94102, San Francisco, CA"},
    {"type": "county", "id": "06075", "label": "San Francisco County, CA"},
    ...
  ]
}
```

#### GET /api/export
Export data as CSV.

**Query Parameters**:
- `geo_type`: "county" or "zipcode"
- `specialty`: Specialty code (or "all")
- `state`: Filter by state (optional)

**Response**: CSV file download.

### 5.2 API Implementation

```python
# api/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import databases
import csv
import io

app = FastAPI(title="Healthcare Dearth Map API")

DATABASE_URL = "postgresql://user:pass@localhost/dearth_map"
database = databases.Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/api/specialties")
async def list_specialties():
    query = "SELECT code, name FROM specialties ORDER BY name"
    rows = await database.fetch_all(query)
    return {"specialties": [dict(r) for r in rows]}

@app.get("/api/counties")
async def list_counties(
    specialty: str = Query(..., description="Specialty code"),
    state: str = Query(None, description="State abbreviation"),
    min_score: float = Query(None),
    max_score: float = Query(None),
):
    query = """
        SELECT 
            c.fips, c.name, c.state_abbr as state, c.population,
            ds.dearth_score, ds.dearth_label, 
            ds.provider_count, ds.provider_density
        FROM counties c
        LEFT JOIN dearth_scores ds 
            ON ds.geo_type = 'county' 
            AND ds.geo_id = c.fips 
            AND ds.specialty_code = :specialty
        WHERE 1=1
    """
    params = {"specialty": specialty}
    
    if state:
        query += " AND c.state_abbr = :state"
        params["state"] = state
    if min_score is not None:
        query += " AND ds.dearth_score >= :min_score"
        params["min_score"] = min_score
    if max_score is not None:
        query += " AND ds.dearth_score <= :max_score"
        params["max_score"] = max_score
    
    query += " ORDER BY ds.dearth_score DESC NULLS LAST"
    
    rows = await database.fetch_all(query, params)
    return {
        "specialty": specialty,
        "count": len(rows),
        "counties": [dict(r) for r in rows]
    }

@app.get("/api/counties/{fips}")
async def get_county(fips: str):
    # Get county info
    county = await database.fetch_one(
        "SELECT * FROM counties WHERE fips = :fips",
        {"fips": fips}
    )
    if not county:
        raise HTTPException(status_code=404, detail="County not found")
    
    # Get all specialty scores
    scores = await database.fetch_all(
        """
        SELECT 
            ds.*, s.name as specialty_name,
            (SELECT AVG(dearth_score) FROM dearth_scores 
             WHERE geo_type='county' AND specialty_code=ds.specialty_code 
             AND geo_id IN (SELECT fips FROM counties WHERE state_abbr=:state)
            ) as state_avg_score,
            (SELECT AVG(dearth_score) FROM dearth_scores 
             WHERE geo_type='county' AND specialty_code=ds.specialty_code
            ) as national_avg_score
        FROM dearth_scores ds
        JOIN specialties s ON s.code = ds.specialty_code
        WHERE ds.geo_type = 'county' AND ds.geo_id = :fips
        ORDER BY s.name
        """,
        {"fips": fips, "state": county["state_abbr"]}
    )
    
    return {
        "fips": county["fips"],
        "name": county["name"],
        "state": county["state_name"],
        "population": county["population"],
        "specialties": [dict(s) for s in scores]
    }
```

---

## 6. Frontend Design

### 6.1 Component Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page (map view)
│   ├── table/
│   │   └── page.tsx            # Table view
│   └── about/
│       └── page.tsx            # Methodology
├── components/
│   ├── Map/
│   │   ├── MapView.tsx         # Main map component
│   │   ├── MapLegend.tsx       # Color legend
│   │   └── MapControls.tsx     # Zoom, reset buttons
│   ├── Panels/
│   │   ├── SpecialtySelector.tsx
│   │   ├── DetailPanel.tsx     # County/zip details
│   │   └── SearchBar.tsx
│   ├── Table/
│   │   ├── DataTable.tsx
│   │   └── ExportButton.tsx
│   └── common/
│       ├── Loading.tsx
│       └── ErrorBoundary.tsx
├── hooks/
│   ├── useCountyData.ts        # Fetch county scores
│   ├── useCountyDetail.ts      # Fetch single county
│   └── useSpecialties.ts       # Fetch specialty list
├── lib/
│   ├── api.ts                  # API client
│   ├── colors.ts               # Color scale functions
│   └── constants.ts
└── types/
    └── index.ts                # TypeScript types
```

### 6.2 Map Component

```tsx
// components/Map/MapView.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { useCountyData } from '@/hooks/useCountyData';

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

interface MapViewProps {
  specialty: string;
  onCountySelect: (fips: string) => void;
}

export function MapView({ specialty, onCountySelect }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const { data, isLoading } = useCountyData(specialty);
  
  useEffect(() => {
    if (!mapContainer.current || map.current) return;
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [-98.5, 39.8], // Center of US
      zoom: 4,
    });
    
    map.current.on('load', () => {
      // Add county boundaries source
      map.current!.addSource('counties', {
        type: 'vector',
        url: 'mapbox://mapbox.82pkq93d', // Mapbox county tileset
      });
      
      // Add choropleth layer
      map.current!.addLayer({
        id: 'county-fills',
        type: 'fill',
        source: 'counties',
        'source-layer': 'original',
        paint: {
          'fill-color': '#ccc',
          'fill-opacity': 0.8,
        },
      });
      
      // Add click handler
      map.current!.on('click', 'county-fills', (e) => {
        if (e.features?.[0]) {
          const fips = e.features[0].properties?.FIPS;
          if (fips) onCountySelect(fips);
        }
      });
    });
    
    return () => map.current?.remove();
  }, []);
  
  // Update colors when data changes
  useEffect(() => {
    if (!map.current || !data?.counties) return;
    
    const colorExpression = buildColorExpression(data.counties);
    map.current.setPaintProperty('county-fills', 'fill-color', colorExpression);
  }, [data]);
  
  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}

function buildColorExpression(counties: Array<{fips: string; dearth_score: number}>) {
  const cases: any[] = ['case'];
  
  for (const county of counties) {
    cases.push(['==', ['get', 'FIPS'], county.fips]);
    cases.push(getColorForScore(county.dearth_score));
  }
  
  cases.push('#ccc'); // default
  return cases;
}

function getColorForScore(score: number): string {
  if (score <= 20) return '#1a9850';  // Dark green
  if (score <= 40) return '#91cf60';  // Light green
  if (score <= 60) return '#fee08b';  // Yellow
  if (score <= 80) return '#fc8d59';  // Orange
  return '#d73027';                    // Red
}
```

### 6.3 Detail Panel

```tsx
// components/Panels/DetailPanel.tsx
'use client';

import { useCountyDetail } from '@/hooks/useCountyDetail';

interface DetailPanelProps {
  fips: string | null;
  onClose: () => void;
}

export function DetailPanel({ fips, onClose }: DetailPanelProps) {
  const { data, isLoading } = useCountyDetail(fips);
  
  if (!fips) return null;
  if (isLoading) return <div className="p-4">Loading...</div>;
  if (!data) return <div className="p-4">County not found</div>;
  
  return (
    <div className="bg-white shadow-lg rounded-lg p-4 w-96">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-xl font-bold">{data.name}</h2>
          <p className="text-gray-600">{data.state}</p>
          <p className="text-sm text-gray-500">
            Population: {data.population.toLocaleString()}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ✕
        </button>
      </div>
      
      <h3 className="font-semibold mb-2">Access by Specialty</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-1">Specialty</th>
            <th className="text-right py-1">Score</th>
            <th className="text-right py-1">vs State</th>
          </tr>
        </thead>
        <tbody>
          {data.specialties.map((s) => (
            <tr key={s.code} className="border-b">
              <td className="py-1">{s.name}</td>
              <td className="text-right">
                <span className={getScoreClass(s.dearth_score)}>
                  {s.dearth_score?.toFixed(1) ?? 'N/A'}
                </span>
              </td>
              <td className="text-right text-xs text-gray-500">
                {s.state_avg_score ? `${(s.dearth_score - s.state_avg_score).toFixed(1)}` : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function getScoreClass(score: number | null): string {
  if (score === null) return 'text-gray-400';
  if (score <= 20) return 'text-green-600 font-semibold';
  if (score <= 40) return 'text-green-500';
  if (score <= 60) return 'text-yellow-600';
  if (score <= 80) return 'text-orange-500';
  return 'text-red-600 font-semibold';
}
```

---

## 7. Deployment

### 7.1 Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐     ┌────────────────┐                      │
│  │    Vercel      │     │   Railway      │                      │
│  │   (Frontend)   │────▶│   (Backend)    │                      │
│  │   Next.js      │     │   FastAPI      │                      │
│  └────────────────┘     └───────┬────────┘                      │
│                                 │                                │
│                                 ▼                                │
│                        ┌────────────────┐                        │
│                        │   Supabase     │                        │
│                        │  (PostgreSQL   │                        │
│                        │   + PostGIS)   │                        │
│                        └────────────────┘                        │
│                                                                  │
│  ┌────────────────┐                                             │
│  │   Cloudflare   │  Static assets, caching                     │
│  │   R2 / S3      │  Raw data files                             │
│  └────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://user:pass@host:5432/dearth_map
OSRM_URL=http://localhost:5000  # Or Google Maps API key
CORS_ORIGINS=https://dearth-map.vercel.app

# Frontend
NEXT_PUBLIC_API_URL=https://api.dearth-map.com
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxx
```

---

## 8. Development Phases

### Phase 1: Data Foundation (Week 1-2)
- [ ] Download NPI full file
- [ ] Parse and filter providers
- [ ] Download Census population data
- [ ] Download county/ZCTA shapefiles
- [ ] Set up PostgreSQL + PostGIS
- [ ] Load geographic data
- [ ] Basic geocoding pipeline

### Phase 2: Core Metrics (Week 3)
- [ ] Implement specialty taxonomy mapping
- [ ] Calculate provider counts by geo/specialty
- [ ] Calculate provider density (per 100k pop)
- [ ] Calculate nearest provider distance
- [ ] Implement Dearth Score formula
- [ ] Populate dearth_scores table

### Phase 3: Drive Time (Week 4)
- [ ] Set up OSRM or Google Maps routing
- [ ] Batch compute drive times
- [ ] Add to Dearth Score calculation
- [ ] Refresh all scores

### Phase 4: Frontend MVP (Week 5-6)
- [ ] Set up Next.js project
- [ ] Implement Mapbox choropleth map
- [ ] Add specialty selector
- [ ] Add county click → detail panel
- [ ] Add color legend
- [ ] Basic styling

### Phase 5: Polish (Week 7)
- [ ] Add search functionality
- [ ] Add table view with sorting
- [ ] Add CSV export
- [ ] Add about/methodology page
- [ ] Performance optimization
- [ ] Mobile responsiveness

### Phase 6: Research Paper (Week 8-9)
- [ ] Document methodology
- [ ] Generate key findings (worst counties by specialty, etc.)
- [ ] Create figures and tables
- [ ] Write paper draft
- [ ] Submit to AMIA / AIiH

---

## 9. Testing Strategy

### Unit Tests
- Dearth Score calculation
- Specialty taxonomy mapping
- API endpoint responses

### Integration Tests
- ETL pipeline end-to-end
- API + database queries
- Frontend + API interaction

### Data Validation
- Compare Dearth Scores to HRSA HPSA designations
- Spot-check known shortage areas
- Verify provider counts against published statistics

---

## 10. Future Enhancements

1. **Real-time appointment data** — Partner with Zocdoc, Healthgrades
2. **Telehealth overlay** — Show where telehealth could bridge gaps
3. **Trend analysis** — Year-over-year changes
4. **Demographic filters** — Age, income, insurance status
5. **Mobile app** — Native iOS/Android
6. **API for researchers** — Public API access
7. **Embedding** — Allow other sites to embed maps

---

*Document ends.*
