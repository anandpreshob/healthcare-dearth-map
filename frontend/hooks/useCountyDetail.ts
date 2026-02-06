import { useQuery } from "@tanstack/react-query";
import { getCountyDetail } from "@/lib/api";

export function useCountyDetail(fips: string | null) {
  return useQuery({
    queryKey: ["county-detail", fips],
    queryFn: () => getCountyDetail(fips!),
    enabled: !!fips,
  });
}
