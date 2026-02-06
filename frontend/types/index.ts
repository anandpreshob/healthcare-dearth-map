export interface Specialty {
  code: string;
  name: string;
}

export interface CountySummary {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  dearth_score: number | null;
  dearth_label: string | null;
  provider_count: number | null;
  provider_density: number | null;
}

export interface SpecialtyScore {
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

export interface CountyDetail {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  specialties: SpecialtyScore[];
}

export interface SearchResult {
  type: string;
  id: string;
  label: string;
}

export interface GeoJSONFeatureProperties {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  dearth_score: number | null;
  dearth_label: string | null;
  provider_count: number | null;
  provider_density: number | null;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: Record<string, unknown>;
  properties: GeoJSONFeatureProperties;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}
