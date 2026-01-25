.PHONY: run search results install help frontend dev-server

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

frontend:
	cd frontend && npm install && npm run dev

dev-server:
	@tmux has-session 2>/dev/null; if [ $$? -ne 0 ]; then tmux new-session -d -s paperpilot; fi
	tmux new-window -t paperpilot: -n "dev" "bash"
	tmux send-keys -t paperpilot:dev.0 "make frontend" C-m
	tmux split-window -v -t paperpilot:dev
	tmux send-keys -t paperpilot:dev.1 "make api" C-m
	tmux attach-session -t paperpilot

# Show help
help:
	uv run paperpilot --help