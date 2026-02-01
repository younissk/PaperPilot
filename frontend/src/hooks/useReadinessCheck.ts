import { useQuery } from "@tanstack/react-query";
import { readinessCheck } from "@/lib/api";

/**
 * Hook to check API readiness status (can accept work now?).
 * Refetches every 10 seconds when window is focused.
 */
export function useReadinessCheck() {
  return useQuery({
    queryKey: ["ready"],
    queryFn: readinessCheck,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
    retry: false,
    staleTime: 5000,
  });
}

