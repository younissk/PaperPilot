/**
 * TypeScript types for Paper Navigator API.
 */

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
  rank?: number;
  elo?: number;
  elo_change?: number;
  wins?: number;
  losses?: number;
  draws?: number;
}

export interface ResearchItem {
  title: string;
  summary: string;
  paper_ids: string[];
}

export interface OpenProblem {
  title: string;
  text: string;
  paper_ids: string[];
}

export interface PaperCard {
  id: string;
  title: string;
  claim: string;
  paradigm_tags: string[];
  year?: number;
  citation_count: number;
  elo_rating?: number;
}

export interface ReportData {
  query: string;
  generated_at: string;
  total_papers_used: number;
  introduction: string;
  current_research: ResearchItem[];
  open_problems: OpenProblem[];
  conclusion: string;
  paper_cards: PaperCard[];
}

export interface SnowballData {
  query: string;
  total_accepted: number;
  papers: Paper[];
}

export interface QueryMetadata {
  query: string;
  created_at?: string;
  last_updated?: string;
  snowball_file?: string;
  snowball_count?: number;
  elo_file?: string;
  report_file?: string;
  report_generated_at?: string;
  report_papers_used?: number;
  report_sections?: number;
}

export interface AllResultsResponse {
  report: ReportData | null;
  graph: Record<string, unknown> | null;
  timeline: Record<string, unknown> | null;
  clusters: Record<string, unknown> | null;
  snowball: SnowballData | null;
}

export interface PipelineRequest {
  query: string;
  num_results?: number;
  max_iterations?: number;
  max_accepted?: number;
  top_n?: number;
  k_factor?: number;
  pairing?: "swiss" | "random";
  early_stop?: boolean;
  elo_concurrency?: number;
  report_top_k?: number;
  notification_email?: string;
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
  report_data?: ReportData | null;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  storage?: string;
  database?: string;
}
