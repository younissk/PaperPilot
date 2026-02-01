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
      const message = error.message.toLowerCase();
      if (message.includes("404") || message.includes("not found")) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });

  const metadataQuery = useQuery({
    queryKey: ["metadata", queryId],
    queryFn: () => getQueryMetadata(queryId!),
    enabled: !!queryId,
    retry: false,
  });

  const errorMessage = resultsQuery.error?.message.toLowerCase() ?? "";
  const notFound = errorMessage.includes("404") || errorMessage.includes("not found");

  return {
    results: resultsQuery.data ?? null,
    metadata: metadataQuery.data?.metadata ?? null,
    isLoading: resultsQuery.isLoading,
    error: notFound ? null : (resultsQuery.error as Error | null),
    notFound,
  };
}
