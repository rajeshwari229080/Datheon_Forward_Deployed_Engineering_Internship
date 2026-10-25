"""Sentinel Governed Agent package for autonomous ERP and CRM operations."""

from sentinel.agent.mock_backend import MockERPBackend
from sentinel.agent.tools import (
    ToolRegistry,
    ToolDefinition,
    ToolCategory,
    InventoryLookupParams,
    CustomerLookupParams,
    LeadStatusUpdateParams,
    SupportTicketCreateParams,
    TicketStatusLookupParams,
    OperationStatusCheckParams,
)
from sentinel.agent.approvals import ApprovalGate, ApprovalStatus
from sentinel.agent.audit import AuditLogger
from sentinel.agent.engine import AgentEngine, ActionTrace, AgentExecutionResult

__all__ = [
    "MockERPBackend",
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "InventoryLookupParams",
    "CustomerLookupParams",
    "LeadStatusUpdateParams",
    "SupportTicketCreateParams",
    "TicketStatusLookupParams",
    "OperationStatusCheckParams",
    "ApprovalGate",
    "ApprovalStatus",
    "AuditLogger",
    "AgentEngine",
    "ActionTrace",
    "AgentExecutionResult",
]
