.PHONY: run search results install help frontend api

# ==============================================================================
# General
# ==============================================================================

# Install dependencies
install:
	uv sync

# Show help
help:
	uv run paperpilot --help

# ==============================================================================
# CLI Commands (local, non-serverless)
# ==============================================================================

# Run a search (use: make search QUERY="your query" N=30)
search:
	uv run paperpilot search "$(or $(QUERY),LLM Based Recommendation Systems)" -n $(or $(N),30)

# Display results (use: make results FILE=snowball_results.json TOP=20)
results:
	uv run paperpilot results $(or $(FILE),snowball_results.json) -t $(or $(TOP),20)

# Run with legacy entry point
run:
	uv run python main.py

# ==============================================================================
# Legacy Local Development (monolith FastAPI)
# ==============================================================================
# NOTE: This runs the deprecated monolith API for local-only workflows.

# Run LEGACY API server directly (use: make api PORT=8000)
api:
	uv run uvicorn paperpilot.api.main:app --reload --port $(or $(PORT),8000)

# Run frontend dev server
frontend:
	cd frontend && npm install && npm run dev
