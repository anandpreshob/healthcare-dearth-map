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
  return fetchJSON<CountySummary[]>(
    `${DATA_BASE}/counties/counties_${code}.json`
  );
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
