import { useMemo } from "react";
import { useGeoJSON } from "./useGeoJSON";
import { getUSCountiesGeoJSON, getUSStatesBorders, getUSNationOutline } from "@/lib/geo";
import { mergeCountyData } from "@/lib/mergeGeoData";
import type { FeatureCollection, Polygon, MultiPolygon, MultiLineString } from "geojson";

// Pre-compute static geometry once at module level
const staticCounties = getUSCountiesGeoJSON();
const stateBorders = getUSStatesBorders();
const nationOutline = getUSNationOutline();

export function useMapData(specialty?: string) {
  const { data: apiData, isLoading, error } = useGeoJSON(specialty);

  const mergedCounties: FeatureCollection<Polygon | MultiPolygon> = useMemo(
    () => mergeCountyData(staticCounties, apiData),
    [apiData]
  );

  return {
    counties: mergedCounties,
    stateBorders,
    nationOutline,
    isLoading,
    error,
  } as {
    counties: FeatureCollection<Polygon | MultiPolygon>;
    stateBorders: MultiLineString;
    nationOutline: MultiLineString;
    isLoading: boolean;
    error: Error | null;
  };
}
