import { Link } from "react-router";
import { SEO } from "@/components";
import { useQueries } from "@/hooks";
import { slugifyQuery } from "@/lib/api";

// Brutalist shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

/**
 * Page listing all previous queries - brutalist design.
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

      <div className="container container-lg py-12 px-4">
        <div className="stack stack-lg">
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

          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16">
              {/* Pulsing Document Loader */}
              <div className="relative">
                <svg
                  width="64"
                  height="82"
                  viewBox="0 0 360 460"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="animate-pulse-brutal"
                >
                  <path
                    d="M340 130H230V20"
                    stroke="black"
                    strokeWidth="20"
                    strokeMiterlimit="10"
                    strokeLinecap="round"
                  />
                  <path
                    d="M350 450H10V10H230L350 130V450Z"
                    stroke="black"
                    strokeWidth="20"
                    strokeMiterlimit="10"
                    strokeLinecap="round"
                  />
                  {/* Animated text lines */}
                  <path
                    d="M280 200H80V220H280V200Z"
                    fill="black"
                    className="animate-line-1"
                  />
                  <path
                    d="M280 320H80V340H280V320Z"
                    fill="black"
                    className="animate-line-2"
                  />
                  <path
                    d="M240 260H80V280H240V260Z"
                    fill="black"
                    className="animate-line-3"
                  />
                </svg>
                {/* Coral shadow that pulses */}
                <div className="absolute inset-0 -z-10 translate-x-1 translate-y-1 bg-coral-shadow animate-pulse-shadow" />
              </div>
              <p className="mt-6 text-gray-600 lowercase tracking-wide animate-fade-in">
                loading queries...
              </p>
            </div>
          )}

          {error && (
            <div className="p-4 border-2 border-black border-l-4 border-l-red-500 bg-white">
              <strong className="lowercase">error:</strong>{" "}
              {error instanceof Error ? error.message : "failed to load queries"}
            </div>
          )}

          {!isLoading && !error && queries.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600 lowercase">no previous queries found.</p>
              <p className="text-sm text-gray-500 lowercase">
                start a search to see your queries here.
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
                    className="flex justify-between items-center bg-white p-6 border-2 border-black no-underline text-inherit transition-all duration-200 hover:no-underline"
                    style={brutalShadow}
                  >
                    <span className="font-medium text-black">{query}</span>
                    <span className="text-black text-xl font-bold">→</span>
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
