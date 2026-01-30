"""Azure Functions entrypoint for PaperPilot."""

from __future__ import annotations

import azure.functions as func

from app.http_routes import bp as http_bp
from app.worker import bp as worker_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_functions(http_bp)
app.register_functions(worker_bp)
