"""Append-only audit event logging for all governed agent actions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_correlation_id, get_logger, redact_sensitive_text

logger = get_logger("sentinel.agent.audit")


class AuditLogger:
    """Manages immutable, append-only audit event trails for compliance."""

    def __init__(self, audit_file_path: Optional[Path] = None):
        settings = get_settings()
        self.file_path = audit_file_path or settings.audit_log_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        tenant_id: str,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        outcome: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Append an audited operational event to disk."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or get_correlation_id() or "none",
            "event_type": event_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "tool_name": tool_name,
            "parameters": redact_sensitive_text(json.dumps(parameters)),
            "outcome": outcome,
            "details": details or {},
        }

        line = json.dumps(payload, default=str) + "\n"
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit event: {str(e)}")
