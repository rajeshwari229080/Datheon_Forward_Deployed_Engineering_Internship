"""Structured logging and correlation ID tracking with sensitive data redaction."""

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable to track correlation IDs across async executions
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(authorization|api[_-]?key|token|secret|password)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{6,})[\"']?"), r"\1=***REDACTED***"),
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "***CARD_REDACTED***"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "***SSN_REDACTED***"),
]


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current async execution context."""
    correlation_id_ctx.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id_ctx.get()


def redact_sensitive_text(text: str) -> str:
    """Mask sensitive keys, tokens, and PII from log output."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class JSONStructuredFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_text(record.getMessage()),
            "correlation_id": get_correlation_id() or "none",
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if provided
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                if k not in log_payload:
                    log_payload[k] = redact_sensitive_text(str(v)) if isinstance(v, str) else v

        return json.dumps(log_payload, default=str)


def get_logger(name: str = "sentinel") -> logging.Logger:
    """Configures and retrieves a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONStructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
