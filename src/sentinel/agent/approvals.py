"""Two-phase cryptographic approval gate with expiry and replay defense."""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.core.models import UserIdentity

logger = get_logger("sentinel.agent.approvals")


class ApprovalStatus(BaseModel):
    operation_id: str
    tenant_id: str
    tool_name: str
    arguments: Dict[str, Any]
    arguments_hash: str
    created_at: float
    expires_at: float
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    is_executed: bool = False
    is_rejected: bool = False
    rejection_reason: Optional[str] = None


class ApprovalGate:
    """Manages sensitive state-changing write approvals using HMAC token signatures."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.secret_key = self.settings.agent_approval_secret.encode("utf-8")
        self.ttl_seconds = self.settings.agent_approval_ttl_seconds
        # In-memory operations ledger: operation_id -> ApprovalStatus
        self._operations: Dict[str, ApprovalStatus] = {}

    def _hash_arguments(self, arguments: Dict[str, Any]) -> str:
        serialized = json.dumps(arguments, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def generate_token(self, operation_id: str, arguments_hash: str, expires_at: float) -> str:
        payload = f"{operation_id}:{arguments_hash}:{expires_at}".encode("utf-8")
        return hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()

    def create_approval_request(
        self,
        tenant_id: str,
        user: UserIdentity,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates a pending operation requiring explicit approval token."""
        now = time.time()
        expires_at = now + self.ttl_seconds
        arg_hash = self._hash_arguments(arguments)
        op_id = f"op_{int(now)}_{arg_hash[:8]}"

        token = self.generate_token(operation_id=op_id, arguments_hash=arg_hash, expires_at=expires_at)

        op_status = ApprovalStatus(
            operation_id=op_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            arguments=arguments,
            arguments_hash=arg_hash,
            created_at=now,
            expires_at=expires_at,
        )
        self._operations[op_id] = op_status

        logger.info(f"Created approval request {op_id} for tool {tool_name} by user {user.user_id}")
        return {
            "status": "APPROVAL_REQUIRED",
            "operation_id": op_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "expires_at": expires_at,
            "approval_token": token,
            "instructions": f"Submit POST /api/v1/approvals/{op_id} with this token to execute the operation.",
        }

    def verify_and_consume(
        self,
        operation_id: str,
        approval_token: str,
        user: UserIdentity,
    ) -> ApprovalStatus:
        """Verifies HMAC signature, checks expiration, and enforces single-use replay protection."""
        op = self._operations.get(operation_id)
        if not op:
            raise ValueError(f"Operation {operation_id} not found.")

        # Enforce tenant isolation
        if op.tenant_id != user.tenant_id:
            raise PermissionError(f"Cross-tenant approval attempt denied for tenant {user.tenant_id}")

        # Check replay protection
        if op.is_executed:
            raise ValueError(f"Operation {operation_id} has already been executed (replay denied).")
        if op.is_rejected:
            raise ValueError(f"Operation {operation_id} has already been rejected.")

        # Check expiry
        now = time.time()
        if now > op.expires_at:
            raise ValueError(f"Approval token for operation {operation_id} has expired.")

        # Check HMAC cryptographic binding
        expected_token = self.generate_token(
            operation_id=operation_id,
            arguments_hash=op.arguments_hash,
            expires_at=op.expires_at,
        )
        if not hmac.compare_digest(expected_token, approval_token):
            raise PermissionError("Invalid or tampered approval token signature.")

        # Consume and mark approved
        op.approved_by = user.user_id
        op.approved_at = now
        op.is_executed = True
        logger.info(f"Approval consumed successfully for operation {operation_id} by {user.user_id}")
        return op

    def get_status(self, operation_id: str) -> Optional[ApprovalStatus]:
        return self._operations.get(operation_id)
