import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { searchLocations } from "@/lib/api";

export function useSearch() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const results = useQuery({
    queryKey: ["search", debouncedQuery],
    queryFn: () => searchLocations(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  return { query, setQuery, results };
}
