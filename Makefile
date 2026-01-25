.PHONY: run search results install help

# Install dependencies
install:
	uv sync

# Run a search (use: make search QUERY="your query" N=30)
search:
	uv run paperpilot search "$(or $(QUERY),LLM Based Recommendation Systems)" -n $(or $(N),30)

# Display results (use: make results FILE=snowball_results.json TOP=20)
results:
	uv run paperpilot results $(or $(FILE),snowball_results.json) -t $(or $(TOP),20)

# Run with legacy entry point
run:
	uv run python main.py

# Run API server (use: make api PORT=8000)
api:
	uv run uvicorn paperpilot.api.main:app --reload --port $(or $(PORT),8000)

# Show help
help:
	uv run paperpilot --help
