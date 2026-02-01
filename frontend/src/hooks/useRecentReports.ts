import { useQuery } from "@tanstack/react-query";
import { getRecentReports } from "@/lib/api";

export function useRecentReports(limit = 5) {
  return useQuery({
    queryKey: ["recent-reports", limit],
    queryFn: () => getRecentReports(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    retry: 1,
  });
}
