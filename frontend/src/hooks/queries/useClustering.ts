import { useMutation, useQuery } from '@tanstack/react-query';
import { startClustering, getClusteringStatus, type ClusteringRequest, type ClusteringResponse } from '../../services/api';

export function useClusteringMutation() {
  return useMutation<ClusteringResponse, Error, ClusteringRequest>({
    mutationFn: startClustering,
  });
}

export function useClusteringStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<ClusteringResponse, Error>({
    queryKey: ['clustering', jobId],
    queryFn: () => getClusteringStatus(jobId!),
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
