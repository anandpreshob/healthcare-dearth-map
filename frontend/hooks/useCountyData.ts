import { useQuery } from "@tanstack/react-query";
import { getCounties } from "@/lib/api";

export function useCountyData(specialty?: string) {
  return useQuery({
    queryKey: ["counties", specialty],
    queryFn: () => getCounties(specialty),
  });
}
