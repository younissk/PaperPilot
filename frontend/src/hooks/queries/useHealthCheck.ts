import { useQuery } from '@tanstack/react-query';
import { healthCheck, type HealthResponse } from '../../services/api';

export function useHealthCheck() {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 1,
  });
}
