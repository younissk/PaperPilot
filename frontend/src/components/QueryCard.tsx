import { Link } from "react-router";
import type { QueryMetadata } from "@/lib/types";
import { slugifyQuery } from "@/lib/api";

// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

interface QueryCardProps {
  query: string;
  metadata?: QueryMetadata | null;
  isLoadingMetadata?: boolean;
}

/**
 * Format a date string to a readable format.
 */
function formatDate(dateString?: string | null): string | null {
  if (!dateString) return null;
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return null;
  }
}

/**
 * Query card component for displaying query information with metadata - brutalist design.
 */
export function QueryCard({ query, metadata, isLoadingMetadata }: QueryCardProps) {
  const slug = slugifyQuery(query);
  const paperCount = metadata?.snowball_count ?? metadata?.report_papers_used;
  const dateStr = formatDate(metadata?.last_updated ?? metadata?.created_at);
  const sectionCount = metadata?.report_sections;
  const hasReport = !!metadata?.report_file || !!metadata?.report_generated_at;

  return (
    <Link
      to={`/report/${slug}`}
      className="block bg-white p-5 border-2 border-black no-underline text-inherit transition-all duration-200 hover:translate-x-0.5 hover:translate-y-0.5 hover:no-underline"
      style={brutalShadow}
    >
      {/* Header row: Title + Paper count badge */}
      <div className="flex justify-between items-start gap-4 mb-3">
        <h3 className="text-lg font-semibold text-black leading-tight flex-1">
          {query}
        </h3>
        {isLoadingMetadata ? (
          <span className="inline-flex items-center px-2 py-1 text-xs font-medium border border-gray-300 bg-gray-100 text-gray-400 animate-pulse">
            ...
          </span>
        ) : paperCount !== undefined && paperCount !== null ? (
          <span
            className="inline-flex items-center px-2 py-1 text-xs font-medium border border-black bg-black text-white whitespace-nowrap"
            style={brutalShadowSmall}
          >
            {paperCount} papers
          </span>
        ) : null}
      </div>

      {/* Metadata row */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center gap-4 flex-wrap">
          {isLoadingMetadata ? (
            <span className="text-gray-400 animate-pulse">loading...</span>
          ) : (
            <>
              {dateStr && (
                <span className="lowercase">
                  <span className="text-gray-400">created:</span> {dateStr}
                </span>
              )}
              {sectionCount !== undefined && sectionCount !== null && (
                <span className="lowercase">
                  <span className="text-gray-400">|</span> {sectionCount} sections
                </span>
              )}
              {hasReport && (
                <span
                  className="inline-flex items-center px-1.5 py-0.5 text-xs border border-green-600 bg-green-50 text-green-700 lowercase"
                >
                  report ready
                </span>
              )}
              {!hasReport && !isLoadingMetadata && (
                <span className="inline-flex items-center px-1.5 py-0.5 text-xs border border-gray-400 bg-gray-50 text-gray-700 lowercase">
                  no report
                </span>
              )}
            </>
          )}
        </div>
        <span className="text-black text-xl font-bold ml-4">→</span>
      </div>
    </Link>
  );
}

/**
 * Skeleton loading state for QueryCard.
 */
export function QueryCardSkeleton() {
  return (
    <div
      className="block bg-white p-5 border-2 border-gray-200 animate-pulse"
      style={{ boxShadow: "3px 3px 0 #e5e5e5" }}
    >
      {/* Header row skeleton */}
      <div className="flex justify-between items-start gap-4 mb-3">
        <div className="h-6 bg-gray-200 rounded flex-1 max-w-[70%]" />
        <div className="h-6 w-20 bg-gray-200 rounded" />
      </div>

      {/* Metadata row skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-4 w-28 bg-gray-200 rounded" />
          <div className="h-4 w-20 bg-gray-200 rounded" />
        </div>
        <div className="h-6 w-6 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
