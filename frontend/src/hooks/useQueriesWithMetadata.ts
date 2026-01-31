import { useQuery, useQueries as useReactQueries } from "@tanstack/react-query";
import { listQueries, getQueryMetadata, slugifyQuery } from "@/lib/api";
import type { QueryMetadata } from "@/lib/types";

export interface QueryWithMetadata {
  query: string;
  slug: string;
  metadata: QueryMetadata | null;
  isLoadingMetadata: boolean;
  metadataError: Error | null;
}

/**
 * Hook to fetch all queries with their metadata.
 * Fetches the query list first, then fetches metadata for each query in parallel.
 */
export function useQueriesWithMetadata() {
  // First, fetch the list of queries
  const queriesResult = useQuery({
    queryKey: ["queries"],
    queryFn: listQueries,
    staleTime: 1000 * 60, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });

  const queries = queriesResult.data?.queries ?? [];

  // Then, fetch metadata for each query in parallel
  const metadataQueries = useReactQueries({
    queries: queries.map((query) => ({
      queryKey: ["queryMetadata", slugifyQuery(query)],
      queryFn: async () => {
        const result = await getQueryMetadata(slugifyQuery(query));
        return { query, metadata: result.metadata };
      },
      staleTime: 1000 * 60 * 5, // 5 minutes for individual metadata
      retry: 1,
      enabled: !!queries.length,
    })),
  });

  // Combine the results
  const queriesWithMetadata: QueryWithMetadata[] = queries.map((query, index) => {
    const metadataResult = metadataQueries[index];
    return {
      query,
      slug: slugifyQuery(query),
      metadata: metadataResult?.data?.metadata ?? null,
      isLoadingMetadata: metadataResult?.isLoading ?? false,
      metadataError: metadataResult?.error as Error | null,
    };
  });

  // Calculate overall loading states
  const isLoadingQueries = queriesResult.isLoading;
  const isLoadingAnyMetadata = metadataQueries.some((q) => q.isLoading);
  const isLoadingAllMetadata = metadataQueries.length > 0 && metadataQueries.every((q) => q.isLoading);

  return {
    // Raw queries list
    queries,
    // Queries with metadata attached
    queriesWithMetadata,
    // Loading states
    isLoading: isLoadingQueries,
    isLoadingQueries,
    isLoadingAnyMetadata,
    isLoadingAllMetadata,
    // Error state (for the initial query list fetch)
    error: queriesResult.error,
    // Refetch function
    refetch: queriesResult.refetch,
  };
}
