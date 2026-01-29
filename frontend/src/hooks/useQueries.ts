import { useQuery } from "@tanstack/react-query";
import { listQueries } from "@/lib/api";

/**
 * Hook to fetch all available queries.
 */
export function useQueries() {
  return useQuery({
    queryKey: ["queries"],
    queryFn: listQueries,
    staleTime: 1000 * 60, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
}
