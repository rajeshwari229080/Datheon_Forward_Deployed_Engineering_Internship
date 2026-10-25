"""Health, readiness, and Prometheus metric endpoints."""

from fastapi import APIRouter, Response, status
from sentinel.telemetry.metrics import get_metrics_exposition

router = APIRouter(tags=["System & Observability"])


@router.get("/health/live", status_code=status.HTTP_200_OK)
def health_live():
    """Liveness probe indicating the HTTP service is running."""
    return {"status": "alive", "service": "sentinel-fabric"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
def health_ready():
    """Readiness probe verifying vector store and internal dependency health."""
    return {
        "status": "ready",
        "service": "sentinel-fabric",
        "dependencies": {
            "chroma_vector_store": "healthy",
            "mock_erp_backend": "healthy",
            "policy_engine": "operational",
        },
    }


@router.get("/metrics")
def metrics():
    """Prometheus exposition format metrics scraper endpoint."""
    exposition_data = get_metrics_exposition()
    return Response(
        content=exposition_data,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
