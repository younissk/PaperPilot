"""FastAPI application for PaperPilot API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paperpilot.api.routes.clustering import router as clustering_router
from paperpilot.api.routes.everything import router as everything_router
from paperpilot.api.routes.graph import router as graph_router
from paperpilot.api.routes.pipeline import router as pipeline_router
from paperpilot.api.routes.ranking import router as ranking_router
from paperpilot.api.routes.report import router as report_router
from paperpilot.api.routes.results import router as results_router
from paperpilot.api.routes.search import router as search_router
from paperpilot.api.routes.timeline import router as timeline_router
from paperpilot.api.schemas import HealthResponse

app = FastAPI(
    title="PaperPilot API",
    description="AI-powered academic literature discovery using snowball sampling",
    version="0.1.0",
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)
app.include_router(results_router)
app.include_router(ranking_router)
app.include_router(clustering_router)
app.include_router(timeline_router)
app.include_router(graph_router)
app.include_router(report_router)
app.include_router(pipeline_router)
app.include_router(everything_router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "PaperPilot API",
        "version": "0.1.0",
        "docs": "/docs",
    }
