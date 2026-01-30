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
    const progress = status.phase_progress ?? 0;
    const total = status.phase_total ?? "?";
    details = `Matches: ${progress} / ${total}`;
  } else if (phase === "report") {
    details = `Step: ${status.phase_step_name || ""}`;
  }

  const leaderboard =
    phase === "ranking" && status.papers
      ? [...status.papers].sort((a, b) => (b.elo ?? 0) - (a.elo ?? 0)).slice(0, 5)
      : [];

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

        {leaderboard.length > 0 && (
          <div className="mt-6 text-left">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Live Leaderboard
            </h3>
            <div className="overflow-hidden rounded-md border border-gray-200">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500">
                  <tr>
                    <th className="px-3 py-2 text-left w-10">#</th>
                    <th className="px-3 py-2 text-left">Paper</th>
                    <th className="px-3 py-2 text-right w-16">ELO</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((paper, idx) => (
                    <tr key={paper.paper_id} className="border-t border-gray-100">
                      <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                      <td className="px-3 py-2 text-gray-700">
                        <span className="block">{paper.title}</span>
                      </td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        {Number.isFinite(paper.elo) ? Math.round(paper.elo) : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
