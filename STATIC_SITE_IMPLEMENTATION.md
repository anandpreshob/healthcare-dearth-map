# Static Site Implementation Plan — GitHub Pages Deployment

## Goal

Convert the Healthcare Dearth Map from a dynamic (FastAPI + PostgreSQL) app to a fully static site deployable on GitHub Pages, while preserving all existing interactivity (map animations, state drill-down, county selection, detail panel, search, table view).

## Why This Works

The frontend already separates **static geometry** (from `us-atlas/counties-10m.json` TopoJSON, loaded client-side in `lib/geo.ts`) from **dynamic data** (dearth scores fetched from the API and merged in `lib/mergeGeoData.ts`). The GeoJSON endpoint (`/api/geojson/counties`) returns features with `"geometry": null` — it only sends score properties, not shapes. All map animations (fitBounds, flyTo, feature-state highlighting) are pure MapLibre GL JS client-side operations. The backend is only used for data retrieval.

## Architecture Overview

```
BEFORE (dynamic):
  Browser → Next.js → FastAPI (6 endpoints) → PostgreSQL + PostGIS

AFTER (static):
  Browser → Next.js static export → Static JSON files on GitHub Pages
```

## Step 1: Create the Static Data Export Script

Create `backend/etl/export_static.py` — a Python script that queries the database and writes all API responses as static JSON files.

### What to export

The script connects to the existing PostgreSQL database and produces these files:

```
frontend/public/data/
├── specialties.json                        # ~500 bytes
├── geojson/
│   ├── counties_primary_care.json          # ~200 KB each
│   ├── counties_cardiology.json
│   ├── counties_neurology.json
│   ├── counties_nephrology.json
│   ├── counties_oncology.json
│   ├── counties_psychiatry.json
│   ├── counties_obgyn.json
│   ├── counties_orthopedics.json
│   ├── counties_general_surgery.json
│   ├── counties_emergency.json
│   ├── counties_radiology.json
│   ├── counties_pathology.json
│   ├── counties_dermatology.json
│   ├── counties_ophthalmology.json
│   └── counties_pediatrics.json            # 15 files total
├── counties/
│   ├── counties_primary_care.json          # same data as geojson but as flat array
│   ├── ... (one per specialty, for table view)
├── details/
│   └── all_counties.json                   # single bundled file, ~2-3 MB
├── search_index.json                       # ~300 KB
└── exports/
    ├── dearth_county_primary_care.csv      # pre-generated CSVs
    ├── ... (one per specialty)
```

### Export script logic

```python
# backend/etl/export_static.py

"""
Export all API data as static JSON files for GitHub Pages deployment.

Usage:
    python -m backend.etl.export_static
    python -m backend.etl.export_static --output-dir ./docs/data
"""

import argparse, json, csv, io, os
import psycopg2
from .config import get_db_params

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'data')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default=OUTPUT_DIR)
    args = parser.parse_args()
    out = args.output_dir

    conn = psycopg2.connect(**get_db_params())

    # Create directory structure
    for subdir in ['geojson', 'counties', 'details', 'exports']:
        os.makedirs(os.path.join(out, subdir), exist_ok=True)

    # 1. specialties.json
    #    Query: SELECT code, name FROM specialties ORDER BY name
    #    Output: [{"code": "cardiology", "name": "Cardiology"}, ...]
    #    Write to: {out}/specialties.json

    # 2. GeoJSON files (one per specialty)
    #    For each specialty code:
    #      Query the county_dearth_summary materialized view:
    #        SELECT fips, name, state_abbr AS state, population,
    #               dearth_score, dearth_label, provider_count, provider_density
    #        FROM county_dearth_summary
    #        WHERE specialty = :code
    #        ORDER BY fips
    #      Format as GeoJSON FeatureCollection with geometry: null
    #      (matching exactly what the /api/geojson/counties endpoint returns)
    #      Write to: {out}/geojson/counties_{code}.json

    # 3. County list files (one per specialty, for table view)
    #    Same query as #2, but output as plain JSON array of objects
    #    (matching what /api/counties?specialty=X returns, sorted by dearth_score DESC)
    #    Write to: {out}/counties/counties_{code}.json

    # 4. County detail bundle (single file with all counties)
    #    For each county FIPS:
    #      Run the same query as the /api/counties/{fips} endpoint:
    #        - County info (fips, name, state, population)
    #        - Per-specialty scores with state and national averages
    #      Bundle into a single dict keyed by FIPS:
    #        {"01001": {"fips": "01001", "name": "...", "specialties": [...]}, ...}
    #    Write to: {out}/details/all_counties.json
    #
    #    IMPORTANT: The state_avg_score and national_avg_score must be pre-computed.
    #    Pre-compute them first:
    #      state_avgs: SELECT specialty_code, c.state_abbr, AVG(dearth_score)
    #                  FROM dearth_scores ds JOIN counties c ON ...
    #                  WHERE geo_type = 'county' GROUP BY specialty_code, state_abbr
    #      natl_avgs:  SELECT specialty_code, AVG(dearth_score)
    #                  FROM dearth_scores WHERE geo_type = 'county'
    #                  GROUP BY specialty_code
    #    Then for each county, look up the averages from these pre-computed dicts.

    # 5. Search index
    #    Query: SELECT fips, name, state_abbr, population FROM counties ORDER BY population DESC
    #    Also:  SELECT zcta, state_abbr, population FROM zipcodes ORDER BY population DESC
    #    Output format:
    #      {"counties": [{"id": "01001", "label": "Autauga, AL", "pop": 58805}, ...],
    #       "zipcodes": [{"id": "35010", "label": "35010 (AL)", "pop": 12345}, ...]}
    #    Write to: {out}/search_index.json

    # 6. Pre-generated CSV exports (one per specialty)
    #    For each specialty, run the same query as the /api/export endpoint
    #    and write a CSV file.
    #    Write to: {out}/exports/dearth_county_{code}.csv

    conn.close()
    print(f"Static export complete. Files written to {out}")
```

The script should use `json.dumps(..., separators=(',', ':'))` (no whitespace) to minimize file sizes. For the details bundle, use float rounding (`round(val, 2)`) to keep the file small.

### Expected file sizes (approximate)

| File | Size (uncompressed) | Size (gzipped) |
|------|--------------------:|---------------:|
| specialties.json | 500 B | 300 B |
| geojson/counties_*.json (×15) | ~200 KB each | ~40 KB each |
| counties/counties_*.json (×15) | ~200 KB each | ~40 KB each |
| details/all_counties.json | ~2.5 MB | ~400 KB |
| search_index.json | ~350 KB | ~80 KB |
| exports/*.csv (×15) | ~300 KB each | ~60 KB each |
| **Total** | **~12 MB** | **~2 MB** |

GitHub Pages has a 1 GB limit per site. This is well within bounds.

---

## Step 2: Modify `lib/api.ts` for Static Data

Replace all fetch calls to point at static JSON files instead of `/api/...` endpoints.

### Current → New mapping

```
/api/specialties                    →  /data/specialties.json
/api/geojson/counties?specialty=X   →  /data/geojson/counties_X.json
/api/counties?specialty=X           →  /data/counties/counties_X.json
/api/counties/{fips}                →  (loaded from bundled /data/details/all_counties.json)
/api/search?q=X                     →  (client-side filter on /data/search_index.json)
/api/export?specialty=X             →  /data/exports/dearth_county_X.csv (direct link)
```

### New `lib/api.ts`

```typescript
import type {
  Specialty,
  CountySummary,
  CountyDetail,
  SearchResult,
  GeoJSONFeatureCollection,
} from "@/types";

// Base path for static data files.
// In production (GitHub Pages), this will be the repo name prefix.
const DATA_BASE = process.env.NEXT_PUBLIC_DATA_BASE || "/data";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Fetch error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function getSpecialties(): Promise<Specialty[]> {
  return fetchJSON<Specialty[]>(`${DATA_BASE}/specialties.json`);
}

export async function getCounties(
  specialty?: string
): Promise<CountySummary[]> {
  const code = specialty || "primary_care";
  return fetchJSON<CountySummary[]>(`${DATA_BASE}/counties/counties_${code}.json`);
}

// --- County detail: loaded from a single bundled JSON file ---
let _detailCache: Record<string, CountyDetail> | null = null;

async function _loadDetailBundle(): Promise<Record<string, CountyDetail>> {
  if (!_detailCache) {
    _detailCache = await fetchJSON<Record<string, CountyDetail>>(
      `${DATA_BASE}/details/all_counties.json`
    );
  }
  return _detailCache;
}

export async function getCountyDetail(fips: string): Promise<CountyDetail> {
  const bundle = await _loadDetailBundle();
  const detail = bundle[fips];
  if (!detail) {
    throw new Error(`County ${fips} not found`);
  }
  return detail;
}

// --- Search: client-side filtering on a pre-loaded index ---
interface SearchIndex {
  counties: Array<{ id: string; label: string; pop: number }>;
  zipcodes: Array<{ id: string; label: string; pop: number }>;
}

let _searchIndex: SearchIndex | null = null;

async function _loadSearchIndex(): Promise<SearchIndex> {
  if (!_searchIndex) {
    _searchIndex = await fetchJSON<SearchIndex>(
      `${DATA_BASE}/search_index.json`
    );
  }
  return _searchIndex;
}

export async function searchLocations(query: string): Promise<SearchResult[]> {
  const index = await _loadSearchIndex();
  const q = query.toLowerCase();
  const results: SearchResult[] = [];

  // Search counties by name (case-insensitive substring match)
  for (const c of index.counties) {
    if (c.label.toLowerCase().includes(q) || c.id.includes(q)) {
      results.push({ type: "county", id: c.id, label: c.label });
      if (results.length >= 10) return results;
    }
  }

  // Search zip codes by prefix
  for (const z of index.zipcodes) {
    if (z.id.startsWith(q)) {
      results.push({ type: "zipcode", id: z.id, label: z.label });
      if (results.length >= 10) return results;
    }
  }

  return results;
}

export async function getGeoJSON(
  specialty?: string
): Promise<GeoJSONFeatureCollection> {
  const code = specialty || "primary_care";
  return fetchJSON<GeoJSONFeatureCollection>(
    `${DATA_BASE}/geojson/counties_${code}.json`
  );
}

export function getExportURL(specialty?: string): string {
  const code = specialty || "primary_care";
  return `${DATA_BASE}/exports/dearth_county_${code}.csv`;
}
```

### What NOT to change

- `hooks/useMapData.ts` — no changes needed. It calls `useGeoJSON()` which calls `getGeoJSON()`, which now fetches static files.
- `hooks/useGeoJSON.ts` — no changes needed.
- `hooks/useCountyDetail.ts` — no changes needed.
- `hooks/useCountyData.ts` — no changes needed.
- `hooks/useSpecialties.ts` — no changes needed.
- `lib/mergeGeoData.ts` — no changes needed.
- `lib/geo.ts` — no changes needed.
- `lib/colors.ts` — no changes needed.
- `lib/constants.ts` — no changes needed.
- `components/` — no changes needed.
- `app/page.tsx` — no changes needed.
- `app/table/page.tsx` — no changes needed.
- `app/about/page.tsx` — no changes needed.

The only files that change are `lib/api.ts` (data source) and `next.config.js` (build config).

---

## Step 3: Modify `hooks/useSearch.ts` for Client-Side Search

The current hook uses React Query to call the API on each debounced keystroke. The new `searchLocations()` in `lib/api.ts` already handles client-side filtering, so the hook itself needs no changes — it will just call the new function. However, we should increase the `staleTime` since the search index is static:

```typescript
// hooks/useSearch.ts — only change staleTime
const results = useQuery({
  queryKey: ["search", debouncedQuery],
  queryFn: () => searchLocations(debouncedQuery),
  enabled: debouncedQuery.length >= 2,
  staleTime: Infinity,  // ADD THIS: search index never changes
});
```

---

## Step 4: Update `next.config.js` for Static Export

Replace the current config (which proxies `/api/` to FastAPI) with a static export config:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",

  // If deploying to github.com/username/healthcare-dearth-map,
  // set basePath to "/healthcare-dearth-map".
  // For a custom domain or github.io root, leave it empty.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",

  // Static assets also need the prefix
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || "",

  // Disable image optimization (not available in static export)
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
```

---

## Step 5: Add Environment Variables

Create `frontend/.env.production`:

```bash
# Set to your GitHub Pages repo path (e.g., /healthcare-dearth-map)
# Leave empty for custom domain or github.io root
NEXT_PUBLIC_BASE_PATH=/healthcare-dearth-map
NEXT_PUBLIC_DATA_BASE=/healthcare-dearth-map/data
```

Create `frontend/.env.development` (for local dev with static data):

```bash
NEXT_PUBLIC_BASE_PATH=
NEXT_PUBLIC_DATA_BASE=/data
```

---

## Step 6: Build and Deploy

### One-time data export (run on the development machine with database access)

```bash
# Make sure the database is running with dearth_scores populated
docker compose up db -d

# Export static data
python -m backend.etl.export_static

# Verify files were created
ls -la frontend/public/data/
ls -la frontend/public/data/geojson/
ls -la frontend/public/data/details/
```

### Build the static site

```bash
cd frontend

# Install dependencies
npm install

# Build static export
npm run build
# This produces the `out/` directory with all static HTML, JS, CSS, and data files

# Test locally
npx serve out
# Open http://localhost:3000/healthcare-dearth-map
```

### Deploy to GitHub Pages

Option A: Manual deploy (simplest)

```bash
# From the frontend directory, after building:
npx gh-pages -d out
```

Option B: GitHub Actions (automated on push)

Create `.github/workflows/deploy.yml`:

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
        with:
          node-version: 20

      - name: Install and build
        working-directory: frontend
        env:
          NEXT_PUBLIC_BASE_PATH: /healthcare-dearth-map
          NEXT_PUBLIC_DATA_BASE: /healthcare-dearth-map/data
        run: |
          npm ci
          npm run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/out

      - uses: actions/deploy-pages@v4
```

Then in the GitHub repo settings → Pages → Source → set to "GitHub Actions".

---

## Step 7: Verify Everything Works

After deployment, test:

1. **Map loads** with primary care choropleth on initial page load
2. **Specialty selector** changes the map colors (triggers fetch of a different `counties_*.json`)
3. **Click on a state** at low zoom → map zooms in with 1200ms animation
4. **Click on a county** at high zoom → detail panel slides in from right with all 15 specialty scores
5. **Search** for a county name → results appear, clicking navigates to county
6. **Table view** (/table) loads and is sortable
7. **Export button** downloads CSV
8. **About page** (/about) renders
9. **Back to US button** works (flyTo animation)
10. **Hover** shows county name tooltip

All of these should work identically to the dynamic version because:
- Map animations are MapLibre client-side (no backend dependency)
- Data format is identical (same JSON shape, just served from files instead of API)
- React Query caching works the same way
- Search is now client-side but returns the same `SearchResult[]` type

---

## Summary of Files Changed

| File | Change |
|------|--------|
| `backend/etl/export_static.py` | **NEW** — data export script |
| `frontend/lib/api.ts` | **REWRITE** — point at static JSON files, add client-side search |
| `frontend/hooks/useSearch.ts` | **MINOR** — add `staleTime: Infinity` |
| `frontend/next.config.js` | **REWRITE** — static export config, remove API proxy |
| `frontend/.env.production` | **NEW** — GitHub Pages base path |
| `frontend/.env.development` | **NEW** — local dev base path |
| `.github/workflows/deploy.yml` | **NEW** — optional CI/CD |

| File | Change |
|------|--------|
| All hooks except useSearch | NO CHANGE |
| All components | NO CHANGE |
| All pages (app/) | NO CHANGE |
| lib/mergeGeoData.ts | NO CHANGE |
| lib/geo.ts | NO CHANGE |
| lib/colors.ts | NO CHANGE |
| lib/constants.ts | NO CHANGE |
| types/index.ts | NO CHANGE |
