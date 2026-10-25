"""Autonomous agent execution and human-in-the-loop approval endpoints."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sentinel.agent.engine import AgentEngine, AgentExecutionResult
from sentinel.core.logging import get_logger
from sentinel.core.models import UserIdentity
from sentinel.core.security import resolve_user_identity
from sentinel.telemetry.metrics import AGENT_OPERATIONS_TOTAL

logger = get_logger("sentinel.api.routes.agent")

router = APIRouter(prefix="/api/v1", tags=["Autonomous Agent & Governance"])

# Shared engine instance
_agent_engine = AgentEngine()


class AgentExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Target registered tool name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Typed parameters for the tool")


class ApprovalSubmitRequest(BaseModel):
    approval_token: str = Field(..., description="Cryptographic HMAC approval token")


@router.post("/agent/execute", response_model=AgentExecutionResult, status_code=status.HTTP_200_OK)
def execute_agent_action(
    payload: AgentExecuteRequest,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Executes a governed agent tool with validation, policy verification, and approval gating."""
    result = _agent_engine.execute_action(
        user=user,
        tool_name=payload.tool_name,
        parameters=payload.parameters,
    )
    AGENT_OPERATIONS_TOTAL.labels(tool_name=payload.tool_name, status=result.status).inc()
    return result


@router.post("/approvals/{operation_id}", response_model=AgentExecutionResult, status_code=status.HTTP_200_OK)
def submit_operation_approval(
    operation_id: str,
    payload: ApprovalSubmitRequest,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Submits an approval token to authorize and trigger execution of a pending write operation."""
    result = _agent_engine.execute_approved_operation(
        user=user,
        operation_id=operation_id,
        approval_token=payload.approval_token,
    )
    stat = "APPROVED_EXECUTED" if result.success else "APPROVAL_FAILED"
    AGENT_OPERATIONS_TOTAL.labels(tool_name="operation_approval", status=stat).inc()
    return result


@router.get("/operations/{operation_id}", status_code=status.HTTP_200_OK)
def get_operation_details(
    operation_id: str,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Check execution status, expiration, and audit record of a specific operation ID."""
    op = _agent_engine.approvals.get_status(operation_id)
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Operation {operation_id} not found.")
    if op.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant operation access denied.")
    return op.model_dump()
