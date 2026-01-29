import { useQuery } from "@tanstack/react-query";
import { getAllResults, getQueryMetadata } from "@/lib/api";
import type { AllResultsResponse, QueryMetadata } from "@/lib/types";

interface UseAllResultsReturn {
  results: AllResultsResponse | null;
  metadata: QueryMetadata | null;
  isLoading: boolean;
  error: Error | null;
  notFound: boolean;
}

/**
 * Hook to fetch all results and metadata for a query.
 */
export function useAllResults(queryId: string | undefined): UseAllResultsReturn {
  const resultsQuery = useQuery({
    queryKey: ["results", queryId],
    queryFn: () => getAllResults(queryId!),
    enabled: !!queryId,
    retry: (failureCount, error) => {
      // Don't retry on 404
      if (error.message.includes("404") || error.message.includes("not found")) {
        return false;
      }
      return failureCount < 2;
    },
  });

  const metadataQuery = useQuery({
    queryKey: ["metadata", queryId],
    queryFn: () => getQueryMetadata(queryId!),
    enabled: !!queryId,
    retry: false,
  });

  const notFound =
    resultsQuery.error?.message.includes("404") ||
    resultsQuery.error?.message.includes("not found") ||
    false;

  return {
    results: resultsQuery.data ?? null,
    metadata: metadataQuery.data?.metadata ?? null,
    isLoading: resultsQuery.isLoading,
    error: notFound ? null : (resultsQuery.error as Error | null),
    notFound,
  };
}
