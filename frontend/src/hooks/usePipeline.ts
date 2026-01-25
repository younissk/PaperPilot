import { useState, useEffect, useCallback, useRef } from "react";
import {
  startPipeline,
  subscribeToPipeline,
  type PipelineRequest,
  type PipelineResponse,
  type PipelineEvent,
  type MatchStats,
  type MatchInfo,
} from "../services/api";

export interface PipelineState {
  jobId: string | null;
  status:
    | "idle"
    | "queued"
    | "searching"
    | "ranking"
    | "reporting"
    | "completed"
    | "failed";
  phase: "search" | "ranking" | "report" | "";
  phaseStep: number;
  phaseStepName: string;
  phaseProgress: number;
  phaseTotal: number;
  progressMessage: string;
  papers: Array<{
    paper_id: string;
    title: string;
    abstract?: string | null;
    year?: number | null;
    citation_count: number;
    rank?: number;
    elo?: number;
    elo_change?: number;
    wins?: number;
    losses?: number;
    draws?: number;
  }>;
  reportData: Record<string, unknown> | null;
  error: string | null;
  // Ranking-specific state
  matchStats: MatchStats | null;
  currentMatch: MatchInfo | null;
  lastMatch: MatchInfo | null;
  // Search-specific state
  currentIteration: number;
  totalIterations: number;
  totalAccepted: number;
  // Query profile (generated during ranking phase, but available for search view)
  queryProfile: Record<string, unknown> | null;
}

const initialState: PipelineState = {
  jobId: null,
  status: "idle",
  phase: "",
  phaseStep: 0,
  phaseStepName: "",
  phaseProgress: 0,
  phaseTotal: 0,
  progressMessage: "",
  papers: [],
  reportData: null,
  error: null,
  matchStats: null,
  currentMatch: null,
  lastMatch: null,
  currentIteration: 0,
  totalIterations: 0,
  totalAccepted: 0,
  queryProfile: null,
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(initialState);
  const eventSourceRef = useRef<EventSource | null>(null);

  const start = useCallback(async (request: PipelineRequest) => {
    try {
      // Reset state
      setState(initialState);

      // Start pipeline
      const response: PipelineResponse = await startPipeline(request);

      setState((prev) => ({
        ...prev,
        jobId: response.job_id,
        status: response.status as PipelineState["status"],
        phase: (response.phase as PipelineState["phase"]) || "",
      }));

      // Subscribe to SSE events
      if (response.job_id) {
        const eventSource = subscribeToPipeline(
          response.job_id,
          (event: PipelineEvent) => {
            setState((prev) => {
              const newState = { ...prev };

              switch (event.type) {
                case "progress":
                  newState.phase =
                    (event.data.phase as PipelineState["phase"]) || prev.phase;
                  newState.phaseStep = event.data.step ?? prev.phaseStep;
                  newState.phaseStepName =
                    event.data.step_name ?? prev.phaseStepName;
                  newState.phaseProgress =
                    event.data.current ?? prev.phaseProgress;
                  newState.phaseTotal = event.data.total ?? prev.phaseTotal;
                  newState.progressMessage =
                    event.data.message ?? prev.progressMessage;

                  // Update search-specific fields
                  if (event.data.current_iteration !== undefined) {
                    newState.currentIteration = event.data.current_iteration;
                  }
                  if (event.data.total_iterations !== undefined) {
                    newState.totalIterations = event.data.total_iterations;
                  }

                  // Update ranking-specific fields
                  if (event.data.papers) {
                    newState.papers = event.data.papers;
                  }
                  if (event.data.match_stats) {
                    newState.matchStats = event.data.match_stats;
                  }
                  if (event.data.current_match !== undefined) {
                    newState.currentMatch = event.data.current_match;
                  }
                  if (event.data.last_match !== undefined) {
                    newState.lastMatch = event.data.last_match;
                  }
                  if (event.data.query_profile !== undefined) {
                    newState.queryProfile = event.data.query_profile as Record<string, unknown>;
                  }

                  // Update status based on phase
                  if (event.data.phase === "search") {
                    newState.status = "searching";
                  } else if (event.data.phase === "ranking") {
                    newState.status = "ranking";
                  } else if (event.data.phase === "report") {
                    newState.status = "reporting";
                  }
                  break;

                case "phase_start":
                  newState.phase =
                    (event.data.phase as PipelineState["phase"]) || prev.phase;
                  if (event.data.phase === "search") {
                    newState.status = "searching";
                  } else if (event.data.phase === "ranking") {
                    newState.status = "ranking";
                  } else if (event.data.phase === "report") {
                    newState.status = "reporting";
                  }
                  break;

                case "phase_complete":
                  if (
                    event.data.phase === "search" &&
                    event.data.papers_found !== undefined
                  ) {
                    // Search phase complete
                    newState.totalAccepted = event.data.papers_found;
                  } else if (
                    event.data.phase === "ranking" &&
                    event.data.papers_ranked !== undefined
                  ) {
                    // Ranking phase complete
                  }
                  break;

                case "complete":
                  newState.status = "completed";
                  if (event.data.papers) {
                    newState.papers = event.data.papers;
                  }
                  if (event.data.report_data) {
                    newState.reportData = event.data.report_data as Record<
                      string,
                      unknown
                    >;
                  }
                  break;

                case "error":
                  newState.status = "failed";
                  newState.error = event.data.error || "Unknown error occurred";
                  break;
              }

              return newState;
            });
          },
        );

        eventSourceRef.current = eventSource;
      }
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: "failed",
        error: err instanceof Error ? err.message : "Failed to start pipeline",
      }));
    }
  }, []);

  const reset = useCallback(() => {
    // Close event source if open
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState(initialState);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    ...state,
    start,
    reset,
    isIdle: state.status === "idle",
    isRunning: ["queued", "searching", "ranking", "reporting"].includes(
      state.status,
    ),
    isCompleted: state.status === "completed",
    isFailed: state.status === "failed",
  };
}
