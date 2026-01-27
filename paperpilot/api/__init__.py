"""PaperPilot API - DEPRECATED monolith FastAPI backend.

WARNING: This module is DEPRECATED and maintained only for local development
convenience. For production, use the serverless API under services/api/.

The monolith API runs all processing synchronously in-process, which is not
suitable for production workloads. Use the serverless architecture instead:

- services/api/handler.py - API Lambda (job creation, status queries)
- services/worker/handler.py - Worker Lambda (async pipeline processing)

To run the legacy monolith locally:
    make api

For production-like local development:
    make dev
"""
