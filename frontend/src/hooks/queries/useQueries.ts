import { useQuery } from '@tanstack/react-query';
import { listQueries, getQueryMetadata, getSnowballResults, type QueryMetadataResponse } from '../../services/api';

export function useQueriesList() {
  return useQuery({
    queryKey: ['queries'],
    queryFn: listQueries,
  });
}

export function useQueryMetadata(query: string | null) {
  return useQuery<QueryMetadataResponse, Error>({
    queryKey: ['query-metadata', query],
    queryFn: () => getQueryMetadata(query!),
    enabled: query !== null,
  });
}

export function useSnowballResults(query: string | null) {
  return useQuery({
    queryKey: ['snowball-results', query],
    queryFn: () => getSnowballResults(query!),
    enabled: query !== null,
  });
}
