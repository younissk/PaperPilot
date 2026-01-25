import { useMutation, useQuery } from '@tanstack/react-query';
import { startSearch, getSearchStatus, type SearchRequest, type SearchResponse } from '../../services/api';

export function useSearchMutation() {
  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: startSearch,
  });
}

export function useSearchStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<SearchResponse, Error>({
    queryKey: ['search', jobId],
    queryFn: () => getSearchStatus(jobId!),
    enabled: enabled && jobId !== null,
    refetchInterval: (data) => {
      // Poll every 2 seconds if job is still running
      if (data?.status === 'queued' || data?.status === 'running') {
        return 2000;
      }
      return false; // Stop polling when completed or failed
    },
    retry: false,
  });
}
