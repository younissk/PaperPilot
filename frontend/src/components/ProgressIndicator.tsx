import { useState, useEffect } from "react";
import type { PipelineResponse, LeaderboardEntry } from "@/lib/types";

interface ProgressIndicatorProps {
  status: PipelineResponse;
  queryTitle?: string;
}

const PHASE_NAMES: Record<string, string> = {
  search: "Searching for Papers",
  ranking: "Ranking Papers",
  report: "Generating Report",
};

const PIPELINE_PHASES = ["search", "ranking", "report"] as const;

/**
 * Format elapsed time as MM:SS or HH:MM:SS
 */
function formatElapsedTime(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Live elapsed timer component
 */
function ElapsedTimer({ createdAt }: { createdAt?: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!createdAt) return;

    const startTime = new Date(createdAt).getTime();

    const updateElapsed = () => {
      const now = Date.now();
      setElapsed(Math.floor((now - startTime) / 1000));
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [createdAt]);

  if (!createdAt) return null;

  return (
    <div className="inline-flex items-center gap-1.5 text-sm text-gray-500">
      <svg
        className="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
      <span className="font-mono">{formatElapsedTime(elapsed)}</span>
    </div>
  );
}

/**
 * Horizontal pipeline timeline showing phase progress
 */
function PipelineTimeline({ currentPhase }: { currentPhase: string }) {
  const currentIndex = PIPELINE_PHASES.indexOf(
    currentPhase as (typeof PIPELINE_PHASES)[number]
  );

  return (
    <div className="flex items-center justify-center gap-0 my-4">
      {PIPELINE_PHASES.map((phase, idx) => {
        const isCompleted = idx < currentIndex;
        const isCurrent = idx === currentIndex;
        const isPending = idx > currentIndex;

        return (
          <div key={phase} className="flex items-center">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
                  transition-all duration-300
                  ${isCompleted ? "bg-primary-500 text-white" : ""}
                  ${isCurrent ? "bg-primary-500 text-white ring-4 ring-primary-100" : ""}
                  ${isPending ? "bg-gray-200 text-gray-400" : ""}
                `}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`
                  text-xs mt-1.5 font-medium
                  ${isCompleted || isCurrent ? "text-primary-600" : "text-gray-400"}
                `}
              >
                {phase === "search" ? "Search" : phase === "ranking" ? "Rank" : "Report"}
              </span>
            </div>

            {/* Connector line (except after last) */}
            {idx < PIPELINE_PHASES.length - 1 && (
              <div
                className={`
                  w-12 h-0.5 mx-1
                  ${idx < currentIndex ? "bg-primary-500" : "bg-gray-200"}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Medal badge for top 3 positions
 */
function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-600 font-bold text-xs medal-gold">
        1
      </span>
    );
  }
  if (rank === 2) {
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-gray-600 font-bold text-xs medal-silver">
        2
      </span>
    );
  }
  if (rank === 3) {
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-600 font-bold text-xs medal-bronze">
        3
      </span>
    );
  }
  return <span className="text-gray-400 font-medium w-6 text-center">{rank}</span>;
}

/**
 * Leaderboard table with enhanced styling
 */
function Leaderboard({ papers }: { papers: LeaderboardEntry[] }) {
  if (papers.length === 0) return null;

  return (
    <div className="mt-6 text-left">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Live Leaderboard
      </h3>
      <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
            <tr>
              <th className="px-3 py-2.5 text-center w-10">#</th>
              <th className="px-3 py-2.5 text-left">Paper</th>
              <th className="px-2 py-2.5 text-center w-10">W</th>
              <th className="px-2 py-2.5 text-center w-10">L</th>
              <th className="px-3 py-2.5 text-right w-16">ELO</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {papers.map((paper, idx) => {
              const rank = idx + 1;
              const isTopThree = rank <= 3;

              return (
                <tr
                  key={paper.paper_id}
                  className={`
                    transition-colors hover:bg-gray-50
                    ${isTopThree ? "bg-gradient-to-r" : ""}
                    ${rank === 1 ? "from-amber-50/50 to-transparent" : ""}
                    ${rank === 2 ? "from-gray-100/50 to-transparent" : ""}
                    ${rank === 3 ? "from-orange-50/50 to-transparent" : ""}
                  `}
                >
                  <td className="px-3 py-2.5 text-center">
                    <RankBadge rank={rank} />
                  </td>
                  <td className="px-3 py-2.5">
                    <span
                      className="block truncate max-w-[200px] text-gray-700 cursor-default"
                      title={paper.title}
                    >
                      {paper.title}
                    </span>
                  </td>
                  <td className="px-2 py-2.5 text-center">
                    <span className="text-green-600 font-medium">
                      {paper.wins ?? "-"}
                    </span>
                  </td>
                  <td className="px-2 py-2.5 text-center">
                    <span className="text-gray-400">
                      {paper.losses ?? "-"}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <span className="font-semibold text-gray-800">
                      {Number.isFinite(paper.elo) ? Math.round(paper.elo) : "-"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Statistics display for the current pipeline run
 */
function PipelineStats({
  phase,
  phaseProgress,
  phaseTotal,
}: {
  phase: string;
  phaseProgress?: number;
  phaseTotal?: number;
}) {
  if (phase !== "ranking" || !phaseProgress || !phaseTotal) return null;

  const matchesRemaining = phaseTotal - phaseProgress;
  const percentComplete = Math.round((phaseProgress / phaseTotal) * 100);

  return (
    <div className="flex justify-center gap-6 mt-3 text-xs text-gray-500">
      <div className="flex items-center gap-1">
        <span className="font-medium text-gray-700">{phaseProgress}</span>
        <span>matches done</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="font-medium text-gray-700">{matchesRemaining}</span>
        <span>remaining</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="font-medium text-gray-700">{percentComplete}%</span>
        <span>complete</span>
      </div>
    </div>
  );
}

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
      <div className="bg-white rounded-xl px-8 py-6 shadow-lg text-center max-w-xl w-full border border-gray-100">
        {/* Header with title and timer */}
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-primary-600 text-xl font-semibold">{title}</h2>
          <ElapsedTimer createdAt={status.created_at} />
        </div>

        {queryTitle && (
          <p className="text-gray-500 text-sm mb-4">
            Generating report for "<span className="font-medium">{queryTitle}</span>"
          </p>
        )}

        {/* Pipeline timeline */}
        <PipelineTimeline currentPhase={phase} />

        {/* Progress bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
          <div
            className="h-full bg-gradient-to-r from-primary-400 to-primary-600 transition-[width] duration-300 ease-out"
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>

        <p className="text-sm text-gray-500">
          {status.progress_message || "Starting..."}
        </p>

        {details && (
          <p className="text-sm text-gray-600 mt-1 font-medium">{details}</p>
        )}

        {/* Statistics */}
        <PipelineStats
          phase={phase}
          phaseProgress={status.phase_progress}
          phaseTotal={status.phase_total}
        />

        {/* Leaderboard */}
        <Leaderboard papers={leaderboard} />
      </div>
    </div>
  );
}
