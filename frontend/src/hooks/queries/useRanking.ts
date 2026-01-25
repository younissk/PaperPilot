import { useMutation, useQuery } from '@tanstack/react-query';
import { startRanking, getRankingStatus, type RankingRequest, type RankingResponse } from '../../services/api';

export function useRankingMutation() {
  return useMutation<RankingResponse, Error, RankingRequest>({
    mutationFn: startRanking,
  });
}

export function useRankingStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<RankingResponse, Error>({
    queryKey: ['ranking', jobId],
    queryFn: () => getRankingStatus(jobId!),
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
