import { useQuery } from "@tanstack/react-query";
import { getAllQueriesMetadata } from "@/lib/api";
import type { QueryMetadata } from "@/lib/types";

export interface QueryWithMetadata {
  query: string;
  slug: string;
  metadata: QueryMetadata | null;
  isLoadingMetadata: boolean;
  metadataError: Error | null;
}

/**
 * Hook to fetch all queries with their metadata in a single batch request.
 * Uses the batch endpoint to avoid N+1 API calls.
 */
export function useQueriesWithMetadata() {
  // Fetch all queries with metadata in a single request
  const result = useQuery({
    queryKey: ["queriesWithMetadata"],
    queryFn: getAllQueriesMetadata,
    staleTime: 1000 * 60, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });

  const queryData = result.data?.queries ?? [];

  // Transform to the expected format
  const queriesWithMetadata: QueryWithMetadata[] = queryData.map((item) => ({
    query: item.query,
    slug: item.slug,
    metadata: item.metadata,
    isLoadingMetadata: false, // All metadata loaded together
    metadataError: null,
  }));

  // Extract just the query names for backwards compatibility
  const queries = queryData.map((item) => item.query);

  return {
    // Raw queries list
    queries,
    // Queries with metadata attached
    queriesWithMetadata,
    // Loading states - now unified since we fetch everything together
    isLoading: result.isLoading,
    isLoadingQueries: result.isLoading,
    isLoadingAnyMetadata: result.isLoading,
    isLoadingAllMetadata: result.isLoading,
    // Error state
    error: result.error,
    // Refetch function
    refetch: result.refetch,
  };
}
