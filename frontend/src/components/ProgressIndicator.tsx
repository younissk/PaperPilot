import type { PipelineResponse } from "@/lib/types";

interface ProgressIndicatorProps {
  status: PipelineResponse;
  queryTitle?: string;
}

const PHASE_NAMES: Record<string, string> = {
  search: "Searching for Papers",
  ranking: "Ranking Papers",
  report: "Generating Report",
};

/**
 * Progress indicator for pipeline jobs.
 */
export function ProgressIndicator({
  status,
  queryTitle,
}: ProgressIndicatorProps) {
  const phase = status.phase || "";
  const title = PHASE_NAMES[phase] || status.status || "Processing...";

  // Calculate progress percentage
  let percent = 0;
  if (status.phase_total && status.phase_progress !== undefined) {
    percent = (status.phase_progress / status.phase_total) * 100;
  }

  // Phase details
  let details = "";
  if (phase === "search") {
    details = `Step: ${status.phase_step_name || ""}`;
  } else if (phase === "ranking") {
    details = `Matches: ${status.phase_progress || 0} / ${status.phase_total || "?"}`;
  } else if (phase === "report") {
    details = `Step: ${status.phase_step_name || ""}`;
  }

  return (
    <div className="flex justify-center items-center min-h-[400px]">
      <div className="bg-white rounded-lg px-12 py-8 shadow-md text-center max-w-lg w-full">
        <h2 className="text-primary-600 mb-2">{title}</h2>
        {queryTitle && (
          <p className="text-gray-500 mb-4">
            Generating report for "{queryTitle}"...
          </p>
        )}

        <div className="h-2 bg-gray-200 rounded overflow-hidden mb-4">
          <div
            className="h-full bg-primary-500 transition-[width] duration-300 ease-out"
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>

        <p className="text-sm text-gray-500">
          {status.progress_message || "Starting..."}
        </p>

        {details && (
          <p className="text-sm text-gray-600 mt-2">{details}</p>
        )}
      </div>
    </div>
  );
}
