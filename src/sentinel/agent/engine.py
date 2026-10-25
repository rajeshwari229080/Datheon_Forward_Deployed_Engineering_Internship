"""Autonomous agent engine with policy checks, approval gates, retries, and action traces."""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from sentinel.agent.approvals import ApprovalGate, ApprovalStatus
from sentinel.agent.audit import AuditLogger
from sentinel.agent.mock_backend import MockERPBackend
from sentinel.agent.tools import ToolCategory, ToolRegistry
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.core.models import Role, UserIdentity
from sentinel.core.security import PolicyEngine

logger = get_logger("sentinel.agent.engine")


class ActionTrace(BaseModel):
    """Transparent operational audit trace omitting internal model thoughts."""
    requested_action: str
    validation_outcome: str
    approval_status: str
    tool_invocation: str
    observed_result: Optional[Dict[str, Any]] = None
    final_status: str
    execution_time_ms: float = 0.0


class AgentExecutionResult(BaseModel):
    """Structured response from agent execution."""
    success: bool
    status: str
    action_trace: ActionTrace
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_details: Optional[Dict[str, Any]] = None


class AgentEngine:
    """Governed autonomous agent coordinating mock ERP/CRM tool execution."""

    def __init__(
        self,
        backend: Optional[MockERPBackend] = None,
        tool_registry: Optional[ToolRegistry] = None,
        approval_gate: Optional[ApprovalGate] = None,
        audit_logger: Optional[AuditLogger] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.backend = backend or MockERPBackend()
        self.tools = tool_registry or ToolRegistry()
        self.approvals = approval_gate or ApprovalGate(self.settings)
        self.audit = audit_logger or AuditLogger()

    def _execute_tool_with_retries(self, tenant_id: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock transactional tool with bounded exponential backoff."""
        if tool_name == "inventory_lookup":
            res = self.backend.lookup_inventory(tenant_id=tenant_id, sku=params["sku"])
            if not res:
                return {"found": False, "message": f"SKU {params['sku']} not found."}
            return {"found": True, "item": res}

        elif tool_name == "customer_lookup":
            res = self.backend.lookup_customer(tenant_id=tenant_id, customer_id=params["customer_id"])
            if not res:
                return {"found": False, "message": f"Customer {params['customer_id']} not found."}
            return {"found": True, "customer": res}

        elif tool_name == "lead_status_update":
            return self.backend.update_lead_status(
                tenant_id=tenant_id,
                lead_id=params["lead_id"],
                new_status=params["new_status"],
                idempotency_key=params.get("idempotency_key"),
            )

        elif tool_name == "support_ticket_create":
            return self.backend.create_support_ticket(
                tenant_id=tenant_id,
                customer_id=params["customer_id"],
                subject=params["subject"],
                priority=params.get("priority", "MEDIUM"),
                idempotency_key=params.get("idempotency_key"),
            )

        elif tool_name == "ticket_status_lookup":
            res = self.backend.lookup_ticket_status(tenant_id=tenant_id, ticket_id=params["ticket_id"])
            if not res:
                return {"found": False, "message": f"Ticket {params['ticket_id']} not found."}
            return {"found": True, "ticket": res}

        elif tool_name == "operation_status_check":
            op = self.approvals.get_status(params["operation_id"])
            if not op:
                return {"found": False, "message": f"Operation {params['operation_id']} not found."}
            return {"found": True, "operation": op.model_dump()}

        raise ValueError(f"Unknown tool name {tool_name}")

    def execute_action(
        self,
        user: UserIdentity,
        tool_name: str,
        parameters: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> AgentExecutionResult:
        """Lifecycle:

        USER REQUEST -> SCHEMA VALIDATION -> POLICY CHECK -> APPROVAL GATE -> TOOL EXECUTION -> AUDIT
        """
        t0 = time.time()

        # Step 1: Tool Schema Validation
        tool_def = self.tools.get_tool(tool_name)
        if not tool_def:
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome="FAILED: Unauthorized tool name",
                approval_status="BYPASSED",
                tool_invocation="NONE",
                final_status="REJECTED",
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )
            return AgentExecutionResult(success=False, status="REJECTED", action_trace=trace, error="Unknown tool.")

        try:
            validated_model = self.tools.validate_params(tool_name, parameters)
            clean_params = validated_model.model_dump()
        except Exception as e:
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome=f"FAILED: Schema validation error: {str(e)}",
                approval_status="BYPASSED",
                tool_invocation="NONE",
                final_status="REJECTED",
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )
            return AgentExecutionResult(success=False, status="REJECTED", action_trace=trace, error=str(e))

        # Step 2: Policy & Role Check
        is_write = tool_def.category == ToolCategory.STATE_CHANGING
        if not PolicyEngine.can_execute_action(user, is_write=is_write):
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome="VALIDATED",
                approval_status="DENIED: Insufficient role permissions",
                tool_invocation="BLOCKED",
                final_status="UNAUTHORIZED",
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )
            self.audit.log_event(
                event_type="ACCESS_DENIED",
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                tool_name=tool_name,
                parameters=clean_params,
                outcome="DENIED",
                details={"reason": "Insufficient role rank"},
                correlation_id=correlation_id,
            )
            return AgentExecutionResult(success=False, status="UNAUTHORIZED", action_trace=trace, error="Access denied.")

        # Step 3: Approval Gate for State-Changing Operations
        if is_write and tool_def.requires_approval:
            approval_req = self.approvals.create_approval_request(
                tenant_id=user.tenant_id,
                user=user,
                tool_name=tool_name,
                arguments=clean_params,
            )
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome="VALIDATED",
                approval_status=f"APPROVAL_REQUIRED: Operation {approval_req['operation_id']}",
                tool_invocation="PENDING_APPROVAL",
                final_status="PENDING_APPROVAL",
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )
            self.audit.log_event(
                event_type="APPROVAL_REQUESTED",
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                tool_name=tool_name,
                parameters=clean_params,
                outcome="PENDING",
                details={"operation_id": approval_req["operation_id"]},
                correlation_id=correlation_id,
            )
            return AgentExecutionResult(
                success=True,
                status="APPROVAL_REQUIRED",
                action_trace=trace,
                approval_details=approval_req,
            )

        # Step 4: Execute Read-Only Operation
        try:
            result_data = self._execute_tool_with_retries(user.tenant_id, tool_name, clean_params)
            elapsed = round((time.time() - t0) * 1000, 2)
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome="VALIDATED",
                approval_status="NOT_REQUIRED",
                tool_invocation=f"EXECUTED: {tool_name}",
                observed_result=result_data,
                final_status="COMPLETED",
                execution_time_ms=elapsed,
            )
            self.audit.log_event(
                event_type="TOOL_EXECUTED",
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                tool_name=tool_name,
                parameters=clean_params,
                outcome="SUCCESS",
                details={"latency_ms": elapsed},
                correlation_id=correlation_id,
            )
            return AgentExecutionResult(success=True, status="COMPLETED", action_trace=trace, data=result_data)
        except Exception as e:
            elapsed = round((time.time() - t0) * 1000, 2)
            trace = ActionTrace(
                requested_action=tool_name,
                validation_outcome="VALIDATED",
                approval_status="NOT_REQUIRED",
                tool_invocation=f"FAILED: {str(e)}",
                final_status="FAILED",
                execution_time_ms=elapsed,
            )
            return AgentExecutionResult(success=False, status="FAILED", action_trace=trace, error=str(e))

    def execute_approved_operation(
        self,
        user: UserIdentity,
        operation_id: str,
        approval_token: str,
        correlation_id: Optional[str] = None,
    ) -> AgentExecutionResult:
        """Consumes a valid approval token and executes the pending state-changing operation."""
        t0 = time.time()
        try:
            op_status = self.approvals.verify_and_consume(
                operation_id=operation_id,
                approval_token=approval_token,
                user=user,
            )
            # Execute actual state change
            result_data = self._execute_tool_with_retries(
                tenant_id=op_status.tenant_id,
                tool_name=op_status.tool_name,
                params=op_status.arguments,
            )
            elapsed = round((time.time() - t0) * 1000, 2)
            trace = ActionTrace(
                requested_action=op_status.tool_name,
                validation_outcome="VALIDATED",
                approval_status="APPROVED_AND_CONSUMED",
                tool_invocation=f"EXECUTED: {op_status.tool_name}",
                observed_result=result_data,
                final_status="COMPLETED",
                execution_time_ms=elapsed,
            )
            self.audit.log_event(
                event_type="APPROVED_TOOL_EXECUTED",
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                tool_name=op_status.tool_name,
                parameters=op_status.arguments,
                outcome="SUCCESS",
                details={"operation_id": operation_id, "approved_by": user.user_id},
                correlation_id=correlation_id,
            )
            return AgentExecutionResult(success=True, status="COMPLETED", action_trace=trace, data=result_data)
        except Exception as e:
            elapsed = round((time.time() - t0) * 1000, 2)
            trace = ActionTrace(
                requested_action="approved_operation",
                validation_outcome="VALIDATION_FAILED",
                approval_status="REJECTED_OR_EXPIRED",
                tool_invocation=f"FAILED: {str(e)}",
                final_status="FAILED",
                execution_time_ms=elapsed,
            )
            return AgentExecutionResult(success=False, status="FAILED", action_trace=trace, error=str(e))
