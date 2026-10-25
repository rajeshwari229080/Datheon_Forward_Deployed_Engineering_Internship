"""Prometheus metrics collectors avoiding high-cardinality PII labels."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Shared global registry
REGISTRY = CollectorRegistry(auto_describe=True)

# 1. HTTP Request Metrics
REQUEST_COUNT = Counter(
    "sentinel_http_requests_total",
    "Total HTTP requests handled by endpoint and status code.",
    ["endpoint", "method", "status"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "sentinel_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# 2. Ingestion & Vector ETL Metrics
INGESTION_DOCUMENTS_TOTAL = Counter(
    "sentinel_ingestion_documents_total",
    "Total ingested files by format and status.",
    ["file_type", "status"],
    registry=REGISTRY,
)

INGESTION_CHUNKS_INDEXED_TOTAL = Counter(
    "sentinel_ingestion_chunks_indexed_total",
    "Total vector chunks indexed into ChromaDB.",
    registry=REGISTRY,
)

# 3. Retrieval & Model Latencies
RETRIEVAL_LATENCY = Histogram(
    "sentinel_retrieval_latency_seconds",
    "Latency of hybrid search retrieval stage in seconds.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
    registry=REGISTRY,
)

MODEL_LATENCY = Histogram(
    "sentinel_model_latency_seconds",
    "Latency of LLM generation stage in seconds.",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

# 4. Agent Governance Metrics
AGENT_OPERATIONS_TOTAL = Counter(
    "sentinel_agent_operations_total",
    "Total autonomous agent tool executions by status.",
    ["tool_name", "status"],
    registry=REGISTRY,
)

# 5. Security & Boundary Guard Metrics
POLICY_VIOLATIONS_TOTAL = Counter(
    "sentinel_policy_violations_total",
    "Security policy violations and unauthorized access attempts.",
    ["violation_type"],
    registry=REGISTRY,
)

ACTIVE_SYSTEM_HEALTH = Gauge(
    "sentinel_system_healthy",
    "1 if system dependencies are healthy, 0 otherwise.",
    registry=REGISTRY,
)
ACTIVE_SYSTEM_HEALTH.set(1)


def get_metrics_exposition() -> bytes:
    """Serialize registered Prometheus metrics to exposition format."""
    return generate_latest(REGISTRY)
