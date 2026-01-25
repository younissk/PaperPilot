/**
 * API client for PaperPilot backend.
 */

import { API_BASE_URL, API_ENDPOINTS } from "../config";

// Type definitions matching API schemas
export interface HealthResponse {
  status: string;
  version: string;
}

export interface SearchRequest {
  query: string;
  num_results?: number;
  max_iterations?: number;
  max_accepted?: number;
  top_n?: number;
}

export interface Paper {
  paper_id: string;
  title: string;
  abstract?: string | null;
  year?: number | null;
  citation_count: number;
  discovered_from?: string | null;
  edge_type: string;
  depth: number;
  judge_reason: string;
  judge_confidence: number;
  // ELO ranking fields (optional, only present in ranked papers)
  rank?: number;
  elo?: number;
  elo_change?: number;
  wins?: number;
  losses?: number;
  draws?: number;
}

export interface SearchResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  total_accepted: number;
  papers: Paper[];
  result_path?: string | null;
  current_step?: number;
  step_name?: string;
  current_progress?: number;
  total_progress?: number;
  progress_message?: string;
  current_iteration?: number;
  total_iterations?: number;
}

export interface RankingRequest {
  query: string;
  file_path?: string | null;
  n_matches?: number | null;
  k_factor?: number;
  pairing?: string;
  early_stop?: boolean;
  concurrency?: number;
  tournament?: boolean;
}

export interface RankingResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  papers: Paper[];
  result_path?: string | null;
  matches_played?: number;
  total_matches?: number;
}

export interface ClusteringRequest {
  query: string;
  file_path?: string | null;
  method?: string;
  n_clusters?: number | null;
  dim_method?: string;
  eps?: number | null;
  min_samples?: number | null;
}

export interface ClusteringResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  clusters_data?: Record<string, unknown> | null;
  html_content?: string | null;
  clusters_json_path?: string | null;
  clusters_html_path?: string | null;
}

export interface TimelineRequest {
  query: string;
  file_path?: string | null;
}

export interface TimelineResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  timeline_data?: Record<string, unknown> | null;
  html_content?: string | null;
  timeline_json_path?: string | null;
  timeline_html_path?: string | null;
}

export interface GraphRequest {
  query: string;
  file_path?: string | null;
  direction?: string;
  limit?: number;
}

export interface GraphResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  graph_data?: Record<string, unknown> | null;
  html_content?: string | null;
  graph_json_path?: string | null;
  graph_html_path?: string | null;
}

export interface ReportRequest {
  query: string;
  file_path?: string | null;
  top_k?: number;
  elo_file_path?: string | null;
}

export interface ReportResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  report_data?: Record<string, unknown> | null;
  report_path?: string | null;
  current_step?: number;
  step_name?: string;
  current_progress?: number;
  total_progress?: number;
  progress_message?: string;
}

export interface PipelineRequest {
  query: string;
  num_results?: number;
  max_iterations?: number;
  max_accepted?: number;
  top_n?: number;
  k_factor?: number;
  pairing?: string;
  early_stop?: boolean;
  elo_concurrency?: number;
  report_top_k?: number;
}

export interface PipelineResponse {
  job_id: string;
  status:
    | "queued"
    | "searching"
    | "ranking"
    | "reporting"
    | "completed"
    | "failed";
  query: string;
  phase?: string;
  phase_step?: number;
  phase_step_name?: string;
  phase_progress?: number;
  phase_total?: number;
  progress_message?: string;
  papers?: Paper[];
  report_data?: Record<string, unknown> | null;
  queryProfile?: Record<string, unknown> | null;
}

export interface MatchStats {
  total_completed: number;
  p1_wins: number;
  p2_wins: number;
  draws: number;
}

export interface MatchInfo {
  paper1_title: string;
  paper2_title: string;
  winner?: number | null;
  reason?: string;
}

export interface PipelineEvent {
  type: "progress" | "phase_start" | "phase_complete" | "complete" | "error";
  data: {
    phase?: string;
    step?: number;
    step_name?: string;
    current?: number;
    total?: number;
    message?: string;
    current_iteration?: number;
    total_iterations?: number;
    papers_found?: number;
    papers_ranked?: number;
    result_path?: string;
    papers?: Paper[];
    report_data?: Record<string, unknown>;
    error?: string;
    // Ranking-specific fields
    match_stats?: MatchStats;
    current_match?: MatchInfo | null;
    last_match?: MatchInfo | null;
    // Query profile
    query_profile?: Record<string, unknown> | null;
  };
}

export interface EverythingRequest {
  query: string;
  file_path?: string | null;
}

export interface EverythingResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  query: string;
  generated_files: string[];
}

export interface QueryListResponse {
  queries: string[];
}

export interface QueryMetadataResponse {
  query: string;
  metadata: Record<string, unknown>;
}

export interface ApiError {
  detail: string;
}

/**
 * Make an API request with error handling.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData: ApiError = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // If JSON parsing fails, use default error message
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Health check endpoint.
 */
export async function healthCheck(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(API_ENDPOINTS.health);
}

/**
 * Search endpoints.
 */
export async function startSearch(
  request: SearchRequest,
): Promise<SearchResponse> {
  return apiRequest<SearchResponse>(API_ENDPOINTS.search, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getSearchStatus(jobId: string): Promise<SearchResponse> {
  return apiRequest<SearchResponse>(`${API_ENDPOINTS.search}/${jobId}`);
}

/**
 * Ranking endpoints.
 */
export async function startRanking(
  request: RankingRequest,
): Promise<RankingResponse> {
  return apiRequest<RankingResponse>(API_ENDPOINTS.ranking, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getRankingStatus(
  jobId: string,
): Promise<RankingResponse> {
  return apiRequest<RankingResponse>(`${API_ENDPOINTS.ranking}/${jobId}`);
}

/**
 * Clustering endpoints.
 */
export async function startClustering(
  request: ClusteringRequest,
): Promise<ClusteringResponse> {
  return apiRequest<ClusteringResponse>(API_ENDPOINTS.clustering, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getClusteringStatus(
  jobId: string,
): Promise<ClusteringResponse> {
  return apiRequest<ClusteringResponse>(`${API_ENDPOINTS.clustering}/${jobId}`);
}

/**
 * Timeline endpoints.
 */
export async function startTimeline(
  request: TimelineRequest,
): Promise<TimelineResponse> {
  return apiRequest<TimelineResponse>(API_ENDPOINTS.timeline, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getTimelineStatus(
  jobId: string,
): Promise<TimelineResponse> {
  return apiRequest<TimelineResponse>(`${API_ENDPOINTS.timeline}/${jobId}`);
}

/**
 * Graph endpoints.
 */
export async function startGraph(
  request: GraphRequest,
): Promise<GraphResponse> {
  return apiRequest<GraphResponse>(API_ENDPOINTS.graph, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getGraphStatus(jobId: string): Promise<GraphResponse> {
  return apiRequest<GraphResponse>(`${API_ENDPOINTS.graph}/${jobId}`);
}

/**
 * Report endpoints.
 */
export async function startReport(
  request: ReportRequest,
): Promise<ReportResponse> {
  return apiRequest<ReportResponse>(API_ENDPOINTS.report, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getReportStatus(jobId: string): Promise<ReportResponse> {
  return apiRequest<ReportResponse>(`${API_ENDPOINTS.report}/${jobId}`);
}

/**
 * Pipeline endpoints (search + ELO + report).
 */
export async function startPipeline(
  request: PipelineRequest,
): Promise<PipelineResponse> {
  return apiRequest<PipelineResponse>(API_ENDPOINTS.pipeline, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getPipelineStatus(
  jobId: string,
): Promise<PipelineResponse> {
  return apiRequest<PipelineResponse>(`${API_ENDPOINTS.pipeline}/${jobId}`);
}

/**
 * Subscribe to pipeline progress via Server-Sent Events (SSE) with reconnection and polling fallback.
 * Returns an EventSource that emits PipelineEvent objects.
 */
export function subscribeToPipeline(
  jobId: string,
  onEvent: (event: PipelineEvent) => void,
): EventSource {
  const url = `${API_BASE_URL}${API_ENDPOINTS.pipeline}/${jobId}/stream`;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let pollingInterval: ReturnType<typeof setInterval> | null = null;
  let isPolling = false;
  let eventSource: EventSource | null = null;

  const startPolling = () => {
    if (isPolling) return;
    isPolling = true;
    console.log("SSE connection lost, falling back to polling...");

    pollingInterval = setInterval(async () => {
      try {
        const status = await getPipelineStatus(jobId);
        
        // Update state from status
        if (status.phase) {
          onEvent({
            type: "progress",
            data: {
              phase: status.phase,
              step: status.phase_step,
              step_name: status.phase_step_name,
              current: status.phase_progress,
              total: status.phase_total,
              message: status.progress_message,
            },
          });
        }

        // Check if job completed or failed
        if (status.status === "completed") {
          onEvent({
            type: "complete",
            data: {
              papers: status.papers || [],
              report_data: status.report_data,
            },
          });
          if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
          }
          isPolling = false;
        } else if (status.status === "failed") {
          // Get error message from status if available
          const errorMsg = (status as any).error || status.progress_message || "Pipeline failed";
          onEvent({
            type: "error",
            data: { error: errorMsg },
          });
          if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
          }
          isPolling = false;
        }
      } catch (err: any) {
        // Check if this is a failed job error
        if (err?.message?.includes("Pipeline failed:")) {
          const errorMsg = err.message.replace("Pipeline failed: ", "");
          onEvent({
            type: "error",
            data: { error: errorMsg },
          });
          if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
          }
          isPolling = false;
        } else {
          console.error("Polling error:", err);
          // Continue polling on other errors (network issues, etc.)
        }
      }
    }, 2000); // Poll every 2 seconds
  };

  const tryReconnect = () => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.log("Max reconnection attempts reached, switching to polling");
      startPolling();
      return;
    }

    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000); // Exponential backoff, max 10s
    
    reconnectTimeout = setTimeout(() => {
      console.log(`Reconnecting SSE (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
      if (eventSource) {
        eventSource.close();
      }
      eventSource = createEventSource();
    }, delay);
  };

  const createEventSource = (): EventSource => {
    const es = new EventSource(url);
    reconnectAttempts = 0; // Reset on successful connection

    es.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ type: "progress", data });
        // Stop polling if SSE is working
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
          isPolling = false;
        }
      } catch (err) {
        console.error("Failed to parse progress event:", err);
      }
    });

    es.addEventListener("phase_start", (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ type: "phase_start", data });
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
          isPolling = false;
        }
      } catch (err) {
        console.error("Failed to parse phase_start event:", err);
      }
    });

    es.addEventListener("phase_complete", (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ type: "phase_complete", data });
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
          isPolling = false;
        }
      } catch (err) {
        console.error("Failed to parse phase_complete event:", err);
      }
    });

    es.addEventListener("complete", (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ type: "complete", data });
        es.close();
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
        }
      } catch (err) {
        console.error("Failed to parse complete event:", err);
      }
    });

    es.addEventListener("query_profile", (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ type: "progress", data: { query_profile: data.query_profile } });
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
          isPolling = false;
        }
      } catch (err) {
        console.error("Failed to parse query_profile event:", err);
      }
    });

    es.addEventListener("error", (e) => {
      try {
        const data = JSON.parse(e.data);
        // This is a server-sent error event (actual pipeline failure)
        onEvent({ type: "error", data });
        es.close();
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
        }
      } catch (err) {
        // If parsing fails, treat as connection error
        console.error("Failed to parse error event:", err);
      }
    });

    es.onerror = () => {
      // Connection error - try to reconnect or poll
      if (es.readyState === EventSource.CLOSED) {
        // Connection closed, try to reconnect
        tryReconnect();
      } else if (es.readyState === EventSource.CONNECTING) {
        // Still connecting, wait
        return;
      } else {
        // Other error, try reconnect
        tryReconnect();
      }
    };

    return es;
  };

  eventSource = createEventSource();

  // Wrap close to include cleanup
  const originalClose = eventSource.close.bind(eventSource);
  const wrappedClose = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
    originalClose();
  };

  // Replace close method
  Object.defineProperty(eventSource, 'close', {
    value: wrappedClose,
    writable: true,
    configurable: true
  });

  return eventSource;
}

/**
 * Everything endpoint.
 */
export async function startEverything(
  request: EverythingRequest,
): Promise<EverythingResponse> {
  return apiRequest<EverythingResponse>(API_ENDPOINTS.everything, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getEverythingStatus(
  jobId: string,
): Promise<EverythingResponse> {
  return apiRequest<EverythingResponse>(`${API_ENDPOINTS.everything}/${jobId}`);
}

/**
 * Results management endpoints.
 */
export async function listQueries(): Promise<QueryListResponse> {
  return apiRequest<QueryListResponse>(API_ENDPOINTS.results);
}

export async function getQueryMetadata(
  query: string,
): Promise<QueryMetadataResponse> {
  return apiRequest<QueryMetadataResponse>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}`,
  );
}

export async function getSnowballResults(
  query: string,
): Promise<{ query: string; total_accepted: number; papers: Paper[] }> {
  return apiRequest<{ query: string; total_accepted: number; papers: Paper[] }>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/snowball`,
  );
}

export async function getEloResults(query: string): Promise<unknown> {
  return apiRequest<unknown>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/elo`,
  );
}

export async function getClustersResults(query: string): Promise<unknown> {
  return apiRequest<unknown>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/clusters`,
  );
}

export async function getTimelineResults(query: string): Promise<unknown> {
  return apiRequest<unknown>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/timeline`,
  );
}

export async function getGraphResults(query: string): Promise<unknown> {
  return apiRequest<unknown>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/graph`,
  );
}

export async function getReportResults(query: string): Promise<unknown> {
  return apiRequest<unknown>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/report`,
  );
}

export interface AllResultsResponse {
  report: Record<string, unknown> | null;
  graph: Record<string, unknown> | null;
  timeline: Record<string, unknown> | null;
  clusters: Record<string, unknown> | null;
  snowball: { query: string; total_accepted: number; papers: Paper[] } | null;
}

export async function getAllResults(
  query: string,
): Promise<AllResultsResponse> {
  return apiRequest<AllResultsResponse>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/all`,
  );
}
