"""FastAPI application factory, middleware, and dependency orchestration."""

import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Dict, List
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentinel.api.routes.health import router as health_router
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger, set_correlation_id
from sentinel.telemetry.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger("sentinel.api.app")

# Sliding-window rate limit ledger: client_ip -> list of timestamps
_rate_limits: Dict[str, List[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and teardown management."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version} in {settings.env} mode")
    yield
    logger.info("Shutting down Sentinel application gracefully.")


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure the production FastAPI application."""
    cfg = settings or get_settings()

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        description="Sentinel Enterprise AI Fabric: Risk-Driven Multi-Tenant RAG, Governed Autonomous Agent & Vector ETL",
        lifespan=lifespan,
    )

    # Secure restricted CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if cfg.env == "development" else ["https://enterprise.internal"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Middleware: Correlation ID, Rate Limiting & Prometheus Instrumentation
    @app.middleware("http")
    async def telemetry_and_security_middleware(request: Request, call_next):
        # 1. Correlation ID
        cid = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:12]}"
        set_correlation_id(cid)

        # 2. Rate Limiting Check
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0
        timestamps = [t for t in _rate_limits[client_ip] if t > window_start]
        if len(timestamps) >= cfg.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded. Try again in 60 seconds.", "correlation_id": cid},
                headers={"X-Correlation-ID": cid},
            )
        timestamps.append(now)
        _rate_limits[client_ip] = timestamps

        # 3. Request timing & handling
        t0 = time.time()
        endpoint = request.url.path
        method = request.method
        try:
            response: Response = await call_next(request)
            elapsed = time.time() - t0
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
            REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=str(response.status_code)).inc()
            response.headers["X-Correlation-ID"] = cid
            return response
        except Exception as exc:
            elapsed = time.time() - t0
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
            REQUEST_COUNT.labels(endpoint=endpoint, method=method, status="500").inc()
            logger.error(f"Unhandled server error on {method} {endpoint}: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "An internal server error occurred.", "correlation_id": cid},
                headers={"X-Correlation-ID": cid},
            )

    # Mount base health routes
    app.include_router(health_router)

    # Mount document ETL routes
    from sentinel.api.routes.documents import router as documents_router
    app.include_router(documents_router)

    # Mount Search & RAG routes
    from sentinel.api.routes.rag import router as rag_router
    app.include_router(rag_router)

    return app


# Default app instance for ASGI servers
app = create_app()
