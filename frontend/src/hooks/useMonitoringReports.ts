import { useQuery } from "@tanstack/react-query";
import { getMonitoringReports } from "@/lib/api";

export function useMonitoringReports(windowDays = 30) {
  return useQuery({
    queryKey: ["monitoring", "reports", windowDays],
    queryFn: () => getMonitoringReports(windowDays),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 15000,
  });
}

