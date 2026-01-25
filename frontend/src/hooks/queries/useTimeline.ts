import { useMutation, useQuery } from '@tanstack/react-query';
import { startTimeline, getTimelineStatus, type TimelineRequest, type TimelineResponse } from '../../services/api';

export function useTimelineMutation() {
  return useMutation<TimelineResponse, Error, TimelineRequest>({
    mutationFn: startTimeline,
  });
}

export function useTimelineStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<TimelineResponse, Error>({
    queryKey: ['timeline', jobId],
    queryFn: () => getTimelineStatus(jobId!),
    enabled: enabled && jobId !== null,
    refetchInterval: (data) => {
      if (data?.status === 'queued' || data?.status === 'running') {
        return 2000;
      }
      return false;
    },
    retry: false,
  });
}
