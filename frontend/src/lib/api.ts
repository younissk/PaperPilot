/**
 * API client for Paper Navigator backend.
 */

import { API_BASE_URL, API_ENDPOINTS } from "./config";
import type {
  HealthResponse,
  ReadinessResponse,
  MonitoringReportsResponse,
  MonitoringPipelinesResponse,
  MonitoringCostsResponse,
  AllResultsResponse,
  AllQueriesMetadataResponse,
  PipelineRequest,
  PipelineResponse,
  QueryMetadata,
  RecentReportsResponse,
  ReportData,
} from "./types";

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
    const statusPrefix = `HTTP ${response.status}`;
    let errorDetail = `${statusPrefix}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      // Support multiple error formats: Azure Functions uses 'error', FastAPI uses 'detail'
      const serverMessage = errorData.error || errorData.detail || errorData.message;
      if (serverMessage) {
        // Preserve HTTP status code for retry logic detection
        errorDetail = `${statusPrefix}: ${serverMessage}`;
      }
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
 * Readiness check endpoint.
 */
export async function readinessCheck(): Promise<ReadinessResponse> {
  return apiRequest<ReadinessResponse>(API_ENDPOINTS.ready);
}

export async function getMonitoringReports(
  windowDays = 30,
): Promise<MonitoringReportsResponse> {
  return apiRequest<MonitoringReportsResponse>(
    `${API_ENDPOINTS.monitoringReports}?window_days=${encodeURIComponent(
      String(windowDays),
    )}`,
  );
}

export async function getMonitoringPipelines(
  windowDays = 30,
): Promise<MonitoringPipelinesResponse> {
  return apiRequest<MonitoringPipelinesResponse>(
    `${API_ENDPOINTS.monitoringPipelines}?window_days=${encodeURIComponent(
      String(windowDays),
    )}`,
  );
}

export async function getMonitoringCosts(
  windowDays = 30,
): Promise<MonitoringCostsResponse> {
  return apiRequest<MonitoringCostsResponse>(
    `${API_ENDPOINTS.monitoringCosts}?window_days=${encodeURIComponent(
      String(windowDays),
    )}`,
  );
}

/**
 * List all queries with results.
 */
export async function listQueries(): Promise<{ queries: string[] }> {
  return apiRequest<{ queries: string[] }>(API_ENDPOINTS.results);
}

/**
 * Get all queries with their metadata in a single batch request.
 * More efficient than fetching metadata for each query individually.
 */
export async function getAllQueriesMetadata(): Promise<AllQueriesMetadataResponse> {
  return apiRequest<AllQueriesMetadataResponse>(
    `${API_ENDPOINTS.results}/metadata`,
  );
}

/**
 * Get metadata for a specific query.
 */
export async function getQueryMetadata(
  query: string,
): Promise<{ query: string; metadata: QueryMetadata }> {
  return apiRequest<{ query: string; metadata: QueryMetadata }>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}`,
  );
}

/**
 * Get all results for a query (report, graph, timeline, clusters, snowball).
 */
export async function getAllResults(
  query: string,
): Promise<AllResultsResponse> {
  return apiRequest<AllResultsResponse>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/all`,
  );
}

/**
 * Get report results for a query.
 */
export async function getReportResults(query: string): Promise<ReportData> {
  return apiRequest<ReportData>(
    `${API_ENDPOINTS.results}/${encodeURIComponent(query)}/report`,
  );
}

/**
 * Get the most recently generated reports with summary metadata.
 */
export async function getRecentReports(
  limit = 5,
): Promise<RecentReportsResponse> {
  return apiRequest<RecentReportsResponse>(
    `${API_ENDPOINTS.results}/recent?limit=${encodeURIComponent(String(limit))}`,
  );
}

/**
 * Start a pipeline job (search + ELO + report).
 */
export async function startPipeline(
  request: PipelineRequest,
): Promise<PipelineResponse> {
  return apiRequest<PipelineResponse>(API_ENDPOINTS.pipeline, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get pipeline job status.
 */
export async function getPipelineStatus(
  jobId: string,
): Promise<PipelineResponse> {
  return apiRequest<PipelineResponse>(`${API_ENDPOINTS.pipeline}/${jobId}`);
}

/**
 * Helper to slugify a query string (matching backend _slugify function).
 */
export function slugifyQuery(query: string): string {
  let slug = query.toLowerCase();
  slug = slug.replace(/[^\w\s-]/g, "");
  slug = slug.replace(/[-\s]+/g, "_");
  slug = slug.replace(/^_+|_+$/g, "");
  if (slug.length > 100) {
    slug = slug.substring(0, 100);
  }
  return slug;
}
