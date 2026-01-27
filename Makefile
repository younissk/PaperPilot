.PHONY: run search results install help frontend dev-server \
       dev dev-stop dev-infra dev-infra-stop dev-infra-logs \
       dev-sam-build dev-api dev-worker dev-check

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
# Legacy Local Development (non-serverless FastAPI)
# ==============================================================================

# Run API server directly (use: make api PORT=8000)
api:
	uv run uvicorn paperpilot.api.main:app --reload --port $(or $(PORT),8000)

# Run frontend dev server
frontend:
	cd frontend && npm install && npm run dev

# Legacy dev server (tmux: frontend + FastAPI direct)
dev-server:
	@tmux has-session 2>/dev/null; if [ $$? -ne 0 ]; then tmux new-session -d -s paperpilot; fi
	tmux new-window -t paperpilot: -n "dev" "bash"
	tmux send-keys -t paperpilot:dev.0 "make frontend" C-m
	tmux split-window -v -t paperpilot:dev
	tmux send-keys -t paperpilot:dev.1 "make api" C-m
	tmux attach-session -t paperpilot

# ==============================================================================
# Serverless Local Development (SAM + LocalStack)
# ==============================================================================

# Environment variables for local development
export AWS_ACCESS_KEY_ID ?= test
export AWS_SECRET_ACCESS_KEY ?= test
export AWS_DEFAULT_REGION ?= eu-central-1
export AWS_ENDPOINT_URL ?= http://localhost:4566
export JOBS_TABLE_NAME ?= paperpilot-jobs-prod
export SQS_QUEUE_URL ?= http://localhost:4566/000000000000/paperpilot-jobs-prod
export LOG_LEVEL ?= DEBUG

# Start LocalStack (DynamoDB + SQS)
dev-infra:
	@echo "Starting LocalStack..."
	docker-compose -f infra/docker-compose.local.yml up -d
	@echo ""
	@echo "Waiting for LocalStack to be ready..."
	@sleep 5
	@echo ""
	@echo "LocalStack is running at http://localhost:4566"
	@echo "Verify with: aws --endpoint-url http://localhost:4566 dynamodb list-tables"

# Stop LocalStack
dev-infra-stop:
	@echo "Stopping LocalStack..."
	docker-compose -f infra/docker-compose.local.yml down

# View LocalStack logs
dev-infra-logs:
	docker-compose -f infra/docker-compose.local.yml logs -f

# Check if LocalStack is ready and resources exist
dev-check:
	@echo "Checking LocalStack status..."
	@curl -s http://localhost:4566/_localstack/health | python3 -m json.tool || echo "LocalStack not running"
	@echo ""
	@echo "DynamoDB tables:"
	@aws --endpoint-url http://localhost:4566 dynamodb list-tables --region eu-central-1 2>/dev/null || echo "  (none or error)"
	@echo ""
	@echo "SQS queues:"
	@aws --endpoint-url http://localhost:4566 sqs list-queues --region eu-central-1 2>/dev/null || echo "  (none or error)"

# Build SAM application
dev-sam-build:
	@echo "Building SAM application..."
	cd infra && sam build

# Start SAM local API (requires dev-infra running)
dev-api:
	@echo "Starting SAM local API on port 8000..."
	@echo "Make sure LocalStack is running (make dev-infra)"
	@echo ""
	cd infra && sam local start-api \
		--port 8000 \
		--env-vars env.local.json \
		--warm-containers EAGER \
		--docker-network host

# Start local worker poller (requires dev-infra running)
dev-worker:
	@echo "Starting local worker poller..."
	@echo "Make sure LocalStack is running (make dev-infra)"
	@echo ""
	uv run python services/worker/local_poller.py

# ==============================================================================
# Full Local Dev Environment (tmux)
# ==============================================================================

# Start full local dev environment with tmux
# Layout: 4 panes - LocalStack logs | SAM API | Worker | Frontend
dev:
	@echo "Starting PaperPilot local development environment..."
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Docker running"
	@echo "  - SAM CLI installed"
	@echo "  - Node.js installed"
	@echo ""
	@# Start LocalStack in background first
	docker-compose -f infra/docker-compose.local.yml up -d
	@echo "Waiting for LocalStack to initialize..."
	@sleep 8
	@# Build SAM application
	@echo "Building SAM application..."
	cd infra && sam build
	@# Create tmux session
	@tmux kill-session -t paperpilot-dev 2>/dev/null || true
	tmux new-session -d -s paperpilot-dev -n "dev"
	@# Pane 0: LocalStack logs
	tmux send-keys -t paperpilot-dev:dev.0 "docker-compose -f infra/docker-compose.local.yml logs -f" C-m
	@# Pane 1: SAM local API (split horizontally)
	tmux split-window -h -t paperpilot-dev:dev
	tmux send-keys -t paperpilot-dev:dev.1 "cd infra && sam local start-api --port 8000 --env-vars env.local.json --warm-containers EAGER --docker-network host" C-m
	@# Pane 2: Worker poller (split pane 1 vertically)
	tmux split-window -v -t paperpilot-dev:dev.1
	tmux send-keys -t paperpilot-dev:dev.2 "sleep 10 && make dev-worker" C-m
	@# Pane 3: Frontend (split pane 0 vertically)
	tmux split-window -v -t paperpilot-dev:dev.0
	tmux send-keys -t paperpilot-dev:dev.3 "make frontend" C-m
	@# Set layout to tiled for even distribution
	tmux select-layout -t paperpilot-dev:dev tiled
	@# Attach to session
	@echo ""
	@echo "Attaching to tmux session 'paperpilot-dev'..."
	@echo "Use 'Ctrl+b d' to detach, 'make dev-stop' to stop all services"
	@echo ""
	tmux attach-session -t paperpilot-dev

# Stop full local dev environment
dev-stop:
	@echo "Stopping PaperPilot local development environment..."
	@# Kill tmux session
	tmux kill-session -t paperpilot-dev 2>/dev/null || true
	@# Stop LocalStack
	docker-compose -f infra/docker-compose.local.yml down
	@echo "Done."