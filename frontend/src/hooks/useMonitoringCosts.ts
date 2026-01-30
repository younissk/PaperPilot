import { useQuery } from "@tanstack/react-query";
import { getMonitoringCosts } from "@/lib/api";

export function useMonitoringCosts(windowDays = 30) {
  return useQuery({
    queryKey: ["monitoring", "costs", windowDays],
    queryFn: () => getMonitoringCosts(windowDays),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 15000,
  });
}

