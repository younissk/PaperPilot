import { useQuery } from "@tanstack/react-query";
import { healthCheck } from "@/lib/api";

/**
 * Hook to check API health status.
 * Refetches every 30 seconds when window is focused.
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: healthCheck,
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    retry: false,
    staleTime: 10000,
  });
}
