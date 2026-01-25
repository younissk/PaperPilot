/**
 * Configuration for the PaperPilot frontend application.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  health: '/api/health',
  search: '/api/search',
  ranking: '/api/ranking',
  clustering: '/api/clustering',
  timeline: '/api/timeline',
  graph: '/api/graph',
  report: '/api/report',
  everything: '/api/everything',
  results: '/api/results',
} as const;

export const DEFAULT_SEARCH_PARAMS = {
  num_results: 5,
  max_iterations: 5,
  max_accepted: 200,
  top_n: 50,
} as const;

export const JOB_POLLING_INTERVAL = 2000; // 2 seconds
