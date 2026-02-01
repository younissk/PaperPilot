import { useQuery } from "@tanstack/react-query";
import { getMonitoringPipelines } from "@/lib/api";

export function useMonitoringPipelines(windowDays = 30) {
  return useQuery({
    queryKey: ["monitoring", "pipelines", windowDays],
    queryFn: () => getMonitoringPipelines(windowDays),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 15000,
  });
}

