import { useMutation, useQuery } from '@tanstack/react-query';
import { startGraph, getGraphStatus, type GraphRequest, type GraphResponse } from '../../services/api';

export function useGraphMutation() {
  return useMutation<GraphResponse, Error, GraphRequest>({
    mutationFn: startGraph,
  });
}

export function useGraphStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<GraphResponse, Error>({
    queryKey: ['graph', jobId],
    queryFn: () => getGraphStatus(jobId!),
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
