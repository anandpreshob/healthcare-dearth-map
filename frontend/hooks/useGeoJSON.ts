import { useQuery } from "@tanstack/react-query";
import { getGeoJSON } from "@/lib/api";

export function useGeoJSON(specialty?: string) {
  return useQuery({
    queryKey: ["geojson", specialty],
    queryFn: () => getGeoJSON(specialty),
    staleTime: 2 * 60 * 1000,
  });
}
