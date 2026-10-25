"""Sentinel telemetry and Prometheus metrics instrumentation."""

from sentinel.telemetry.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    INGESTION_DOCUMENTS_TOTAL,
    RETRIEVAL_LATENCY,
    MODEL_LATENCY,
    AGENT_OPERATIONS_TOTAL,
    POLICY_VIOLATIONS_TOTAL,
    get_metrics_exposition,
)

__all__ = [
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "INGESTION_DOCUMENTS_TOTAL",
    "RETRIEVAL_LATENCY",
    "MODEL_LATENCY",
    "AGENT_OPERATIONS_TOTAL",
    "POLICY_VIOLATIONS_TOTAL",
    "get_metrics_exposition",
]
