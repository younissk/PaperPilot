.PHONY: install test lint frontend

# ==============================================================================
# General
# ==============================================================================

# Install dependencies
install:
	uv sync

# Run tests
test:
	uv run pytest tests/ -v

# Run linter
lint:
	uv run ruff check papernavigator azure-functions tests
	uv run pyright

# ==============================================================================
# Frontend Development
# ==============================================================================

# Run frontend dev server
frontend:
	cd frontend && npm install && npm run dev
