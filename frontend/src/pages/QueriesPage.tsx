import { useState, useMemo } from "react";
import { Link } from "react-router";
import { SEO, QueryCard, QueryCardSkeleton } from "@/components";
import { useQueriesWithMetadata } from "@/hooks";

// Brutalist shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

/**
 * Page listing all previous queries with search functionality - brutalist design.
 */
export default function QueriesPage() {
  const { queriesWithMetadata, isLoading, error } = useQueriesWithMetadata();
  const [searchTerm, setSearchTerm] = useState("");

  // Filter queries based on search term
  const filteredQueries = useMemo(() => {
    if (!searchTerm.trim()) {
      return queriesWithMetadata;
    }
    const lowerSearch = searchTerm.toLowerCase();
    return queriesWithMetadata.filter((q) =>
      q.query.toLowerCase().includes(lowerSearch)
    );
  }, [queriesWithMetadata, searchTerm]);

  const hasQueries = queriesWithMetadata.length > 0;
  const showingFiltered = searchTerm.trim() && filteredQueries.length !== queriesWithMetadata.length;

  return (
    <>
      <SEO
        title="Previous Searches"
        description="View and explore your previous research queries."
      />

      <div className="container container-lg py-12 px-4">
        <div className="stack stack-lg">
          {/* Header */}
          <div className="flex justify-between items-center flex-wrap gap-4">
            <h1 className="text-3xl md:text-4xl font-bold text-black text-shadow-brutal lowercase">
              previous searches
            </h1>
            <Link
              to="/"
              className="btn btn-brutal lowercase"
              style={brutalShadow}
            >
              new search
            </Link>
          </div>

          {/* Search Bar */}
          {hasQueries && !isLoading && (
            <div className="relative">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <circle cx="11" cy="11" r="8" />
                      <path d="m21 21-4.3-4.3" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="search queries..."
                    className="w-full pl-10 pr-10 py-3 border-2 border-black bg-white text-black placeholder-gray-400 lowercase focus:outline-none focus:ring-0 transition-shadow"
                    style={brutalShadow}
                  />
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black transition-colors"
                      aria-label="Clear search"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M18 6 6 18" />
                        <path d="m6 6 12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
              {/* Result count */}
              {showingFiltered && (
                <p className="mt-2 text-sm text-gray-500 lowercase">
                  showing {filteredQueries.length} of {queriesWithMetadata.length} queries
                </p>
              )}
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col gap-4">
              <QueryCardSkeleton />
              <QueryCardSkeleton />
              <QueryCardSkeleton />
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-4 border-2 border-black border-l-4 border-l-red-500 bg-white">
              <strong className="lowercase">error:</strong>{" "}
              {error instanceof Error ? error.message : "failed to load queries"}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && queriesWithMetadata.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600 lowercase">no previous queries found.</p>
              <p className="text-sm text-gray-500 lowercase">
                start a search to see your queries here.
              </p>
            </div>
          )}

          {/* No Search Results */}
          {!isLoading && !error && queriesWithMetadata.length > 0 && filteredQueries.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600 lowercase">
                no queries match "{searchTerm}"
              </p>
              <button
                onClick={() => setSearchTerm("")}
                className="mt-2 text-sm text-coral-shadow hover:underline lowercase"
              >
                clear search
              </button>
            </div>
          )}

          {/* Query Cards */}
          {!isLoading && !error && filteredQueries.length > 0 && (
            <div className="flex flex-col gap-4">
              {filteredQueries.map((item) => (
                <QueryCard
                  key={item.slug}
                  query={item.query}
                  metadata={item.metadata}
                  isLoadingMetadata={item.isLoadingMetadata}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
