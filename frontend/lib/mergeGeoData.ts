import type { FeatureCollection, Polygon, MultiPolygon } from "geojson";
import type { GeoJSONFeatureCollection } from "@/types";

export interface MergedProperties {
  fips: string;
  name: string;
  state: string;
  population: number | null;
  dearth_score: number | null;
  dearth_label: string | null;
  provider_count: number | null;
  provider_density: number | null;
  hasData: boolean;
}

/**
 * Merge static us-atlas county geometry with API dearth scores.
 * Counties without API data get hasData: false and null scores.
 */
export function mergeCountyData(
  staticCounties: FeatureCollection<Polygon | MultiPolygon>,
  apiData?: GeoJSONFeatureCollection
): FeatureCollection<Polygon | MultiPolygon> {
  // Build lookup from API data keyed by FIPS
  const apiLookup = new Map<string, Record<string, unknown>>();
  if (apiData) {
    for (const f of apiData.features) {
      const fips = f.properties.fips;
      if (fips) apiLookup.set(fips, f.properties as unknown as Record<string, unknown>);
    }
  }

  const merged: FeatureCollection<Polygon | MultiPolygon> = {
    type: "FeatureCollection",
    features: staticCounties.features.map((f, idx) => {
      const fips = (f.properties as Record<string, unknown>)?.fips as string;
      const apiProps = fips ? apiLookup.get(fips) : undefined;

      const props: MergedProperties = apiProps
        ? {
            fips,
            name: (apiProps.name as string) ?? fips,
            state: (apiProps.state as string) ?? "",
            population: (apiProps.population as number | null) ?? null,
            dearth_score: (apiProps.dearth_score as number | null) ?? null,
            dearth_label: (apiProps.dearth_label as string | null) ?? null,
            provider_count: (apiProps.provider_count as number | null) ?? null,
            provider_density: (apiProps.provider_density as number | null) ?? null,
            hasData: true,
          }
        : {
            fips,
            name: fips,
            state: "",
            population: null,
            dearth_score: null,
            dearth_label: null,
            provider_count: null,
            provider_density: null,
            hasData: false,
          };

      return {
        ...f,
        id: idx,
        properties: props as unknown as Record<string, unknown>,
      };
    }),
  };

  return merged;
}
