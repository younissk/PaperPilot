"""PaperPilot API - DEPRECATED monolith FastAPI backend.

WARNING: This module is DEPRECATED and maintained only for local development
convenience. For production, use the Azure Functions backend under
`azure-functions/`.

The monolith API runs all processing synchronously in-process, which is not
suitable for production workloads. Use the serverless architecture instead:

- azure-functions/function_app.py - Function entrypoint (HTTP + Service Bus)

To run the legacy monolith locally:
    make api
"""
