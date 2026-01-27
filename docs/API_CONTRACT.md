# PaperPilot API Contract

This document defines the API contract between the frontend (Astro SSR) and the serverless backend (API Lambda).

## Overview

The frontend expects these endpoints from the backend. The **serverless API** (`services/api/handler.py`) is the source of truth for production deployments.

## Required Endpoints

### Health Check

```
GET /api/health
```

**Response** (`HealthResponse`):
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Used by**: `Header.astro` (status indicator)

---

### Pipeline Operations

#### Start Pipeline Job

```
POST /api/pipeline
```

**Request** (`PipelineRequest`):
```json
{
  "query": "LLM Based Recommendation Systems",
  "num_results": 5,
  "max_iterations": 5,
  "max_accepted": 200,
  "top_n": 50,
  "k_factor": 32.0,
  "pairing": "swiss",
  "early_stop": true,
  "elo_concurrency": 5,
  "report_top_k": 30
}
```

**Response** (`PipelineResponse`, HTTP 202):
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "Pipeline job queued for processing"
}
```

**Used by**: `index.astro` (search form submit)

---

#### Get Pipeline Job Status

```
GET /api/pipeline/{job_id}
```

**Response** (`PipelineResponse`):
```json
{
  "job_id": "uuid-string",
  "status": "running|completed|failed|queued",
  "query": "LLM Based Recommendation Systems",
  "phase": "search|ranking|report",
  "phase_step": 2,
  "phase_step_name": "Snowball iteration",
  "phase_progress": 15,
  "phase_total": 50,
  "progress_message": "Processing iteration 2 of 5...",
  "papers": [...],
  "report_data": {...},
  "error": null
}
```

**Used by**: `report/[query_id].astro` (polling during generation)

> **Note**: The serverless API currently has `GET /api/jobs/{job_id}`. This endpoint needs to be aliased or the response shape needs to be mapped for frontend compatibility.

---

### Results Operations

#### List Available Queries

```
GET /api/results
```

**Response**:
```json
{
  "queries": ["LLM Based Recommendation Systems", "AI in Healthcare", ...]
}
```

**Used by**: `queries.astro` (list previous searches)

---

#### Get Query Metadata

```
GET /api/results/{query_slug}
```

**Response**:
```json
{
  "query": "llm_based_recommender_systems",
  "metadata": {
    "query": "LLM Based Recommendation Systems",
    "created_at": "2024-01-01T00:00:00Z",
    "last_updated": "2024-01-01T00:05:00Z",
    "snowball_file": "snowball.json",
    "snowball_count": 150,
    "elo_file": "elo_ranked_k32_pswiss.json",
    "report_file": "report_top_k30.json",
    "report_generated_at": "2024-01-01T00:05:00Z",
    "report_papers_used": 30,
    "report_sections": 5
  }
}
```

**Used by**: `report/[query_id].astro` (metadata display)

---

#### Get All Results for Query

```
GET /api/results/{query_slug}/all
```

**Response** (`AllResultsResponse`):
```json
{
  "report": {
    "query": "LLM Based Recommendation Systems",
    "generated_at": "2024-01-01T00:05:00Z",
    "total_papers_used": 30,
    "introduction": "...",
    "current_research": [...],
    "open_problems": [...],
    "conclusion": "...",
    "paper_cards": [...]
  },
  "graph": null,
  "timeline": null,
  "clusters": null,
  "snowball": {
    "query": "...",
    "total_accepted": 150,
    "papers": [...]
  }
}
```

**Used by**: `report/[query_id].astro` (main report page)

---

#### Get Report Only

```
GET /api/results/{query_slug}/report
```

**Response** (`ReportData`):
```json
{
  "query": "LLM Based Recommendation Systems",
  "generated_at": "2024-01-01T00:05:00Z",
  "total_papers_used": 30,
  "introduction": "...",
  "current_research": [...],
  "open_problems": [...],
  "conclusion": "...",
  "paper_cards": [...]
}
```

**Used by**: `api.ts` (available but may not be actively used)

---

## Implementation Status

| Endpoint | Serverless API | Notes |
|----------|----------------|-------|
| `GET /api/health` | ✅ Implemented | Works as expected |
| `POST /api/pipeline` | ✅ Implemented | Works as expected |
| `GET /api/pipeline/{job_id}` | ✅ Implemented | Maps DynamoDB job to frontend format |
| `GET /api/results` | ✅ Implemented | Lists query slugs from S3 |
| `GET /api/results/{query}` | ✅ Implemented | Returns query metadata from S3 |
| `GET /api/results/{query}/all` | ✅ Implemented | Returns all results (report, snowball, etc.) |
| `GET /api/results/{query}/report` | ✅ Implemented | Returns just the report |

## Type Definitions

See `frontend/src/lib/types.ts` for TypeScript definitions that correspond to these API responses.

## Query Slug Format

Queries are slugified for URL paths using this algorithm:
1. Convert to lowercase
2. Remove non-word characters (except spaces and hyphens)
3. Replace spaces/hyphens with underscores
4. Strip leading/trailing underscores
5. Truncate to 100 characters

Example: `"LLM Based Recommendation Systems"` → `"llm_based_recommender_systems"`
