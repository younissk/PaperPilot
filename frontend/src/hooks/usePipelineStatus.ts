import { useQuery } from "@tanstack/react-query";
import { getPipelineStatus } from "@/lib/api";
import { JOB_POLLING_INTERVAL } from "@/lib/config";

/**
 * Hook to poll pipeline job status.
 * Automatically stops polling when job is completed or failed.
 */
export function usePipelineStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["pipeline", jobId],
    queryFn: () => getPipelineStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling when job is done
      if (status === "completed" || status === "failed") {
        return false;
      }
      return JOB_POLLING_INTERVAL;
    },
    staleTime: 0, // Always refetch
  });
}
