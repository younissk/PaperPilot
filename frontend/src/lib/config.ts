/**
 * Configuration for the Paper Navigator frontend.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://api.papernavigator.com";

export const API_ENDPOINTS = {
  health: "/api/health",
  ready: "/api/ready",
  search: "/api/search",
  ranking: "/api/ranking",
  clustering: "/api/clustering",
  timeline: "/api/timeline",
  graph: "/api/graph",
  report: "/api/report",
  pipeline: "/api/pipeline",
  everything: "/api/everything",
  results: "/api/results",
  monitoringReports: "/api/monitoring/reports",
  monitoringPipelines: "/api/monitoring/pipelines",
  monitoringCosts: "/api/monitoring/costs",
} as const;

export const DEFAULT_PIPELINE_PARAMS = {
  num_results: 5,
  max_iterations: 5,
  max_accepted: 200,
  top_n: 50,
  k_factor: 32.0,
  pairing: "swiss" as const,
  early_stop: true,
  elo_concurrency: 5,
  report_top_k: 30,
} as const;

export const JOB_POLLING_INTERVAL = 2000;
