import { useQuery } from "@tanstack/react-query";
import { getSpecialties } from "@/lib/api";

export function useSpecialties() {
  return useQuery({
    queryKey: ["specialties"],
    queryFn: getSpecialties,
    staleTime: 5 * 60 * 1000,
  });
}
