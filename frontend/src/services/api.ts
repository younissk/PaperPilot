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
