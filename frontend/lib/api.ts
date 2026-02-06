import type {
  Specialty,
  CountySummary,
  CountyDetail,
  SearchResult,
  GeoJSONFeatureCollection,
} from "@/types";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function getSpecialties(): Promise<Specialty[]> {
  return fetchJSON<Specialty[]>("/api/specialties");
}

export async function getCounties(
  specialty?: string
): Promise<CountySummary[]> {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "?specialty=primary_care";
  return fetchJSON<CountySummary[]>(`/api/counties${params}`);
}

export async function getCountyDetail(fips: string): Promise<CountyDetail> {
  return fetchJSON<CountyDetail>(`/api/counties/${fips}`);
}

export async function searchLocations(query: string): Promise<SearchResult[]> {
  return fetchJSON<SearchResult[]>(
    `/api/search?q=${encodeURIComponent(query)}`
  );
}

export async function getGeoJSON(
  specialty?: string
): Promise<GeoJSONFeatureCollection> {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "?specialty=primary_care";
  return fetchJSON<GeoJSONFeatureCollection>(
    `/api/geojson/counties${params}`
  );
}

export function getExportURL(specialty?: string): string {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "?specialty=primary_care";
  return `/api/export${params}`;
}
