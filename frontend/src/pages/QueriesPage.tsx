import { Link } from "react-router";
import { SEO } from "@/components";
import { useQueries } from "@/hooks";
import { slugifyQuery } from "@/lib/api";

/**
 * Page listing all previous queries.
 */
export default function QueriesPage() {
  const { data, isLoading, error } = useQueries();
  const queries = data?.queries || [];

  return (
    <>
      <SEO
        title="Previous Searches"
        description="View and explore your previous research queries."
      />

      <div className="container container-lg">
        <div className="stack stack-lg">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <h1>Previous Searches</h1>
            <Link to="/" className="btn btn-primary">
              New Search
            </Link>
          </div>

          {isLoading && (
            <div className="text-center py-12">
              <div className="spinner mx-auto mb-4" />
              <p className="text-gray-500">Loading queries...</p>
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong>{" "}
              {error instanceof Error ? error.message : "Failed to load queries"}
            </div>
          )}

          {!isLoading && !error && queries.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No previous queries found.</p>
              <p className="text-sm text-gray-500">
                Start a search to see your queries here.
              </p>
            </div>
          )}

          {!isLoading && !error && queries.length > 0 && (
            <div className="flex flex-col gap-4">
              {queries.map((query) => {
                const slug = slugifyQuery(query);
                return (
                  <Link
                    key={slug}
                    to={`/report/${slug}`}
                    className="flex justify-between items-center bg-white p-6 rounded-md border border-gray-200 no-underline text-inherit transition-all duration-200 hover:border-primary-400 hover:shadow-md hover:no-underline"
                  >
                    <span className="font-medium">{query}</span>
                    <span className="text-primary-600 text-xl">→</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
