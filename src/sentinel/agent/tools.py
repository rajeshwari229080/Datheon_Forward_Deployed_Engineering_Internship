"""Typed tool registry and Pydantic parameter schemas for governed operations."""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError


class ToolCategory(str, Enum):
    READ_ONLY = "read_only"
    STATE_CHANGING = "state_changing"


# Parameter schemas
class InventoryLookupParams(BaseModel):
    sku: str = Field(..., description="Unique product SKU (e.g., SKU-1001)")


class CustomerLookupParams(BaseModel):
    customer_id: str = Field(..., description="Unique customer ID (e.g., CUST-001)")


class LeadStatusUpdateParams(BaseModel):
    lead_id: str = Field(..., description="Unique lead ID (e.g., LEAD-501)")
    new_status: str = Field(..., description="Target status: NEW, CONTACTED, QUALIFIED, LOST, CONVERTED")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key for replay defense")


class SupportTicketCreateParams(BaseModel):
    customer_id: str = Field(..., description="Customer ID creating the ticket")
    subject: str = Field(..., min_length=5, description="Ticket subject title")
    priority: str = Field("MEDIUM", description="Ticket priority: LOW, MEDIUM, HIGH, CRITICAL")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key for replay defense")


class TicketStatusLookupParams(BaseModel):
    ticket_id: str = Field(..., description="Ticket ID (e.g., TCK-9001)")


class OperationStatusCheckParams(BaseModel):
    operation_id: str = Field(..., description="Operation ID to verify")


class ToolDefinition(BaseModel):
    """Explicit tool registry definition."""
    name: str
    description: str
    category: ToolCategory
    param_model: Type[BaseModel]
    requires_approval: bool = False

    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """Explicit allowlist of authorized agent tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(
            ToolDefinition(
                name="inventory_lookup",
                description="Look up product catalog stock, warehouse location, and pricing by SKU.",
                category=ToolCategory.READ_ONLY,
                param_model=InventoryLookupParams,
                requires_approval=False,
            )
        )
        self.register(
            ToolDefinition(
                name="customer_lookup",
                description="Look up customer tier, credit limit, and contact info by customer ID.",
                category=ToolCategory.READ_ONLY,
                param_model=CustomerLookupParams,
                requires_approval=False,
            )
        )
        self.register(
            ToolDefinition(
                name="lead_status_update",
                description="Update the sales status of an existing CRM lead.",
                category=ToolCategory.STATE_CHANGING,
                param_model=LeadStatusUpdateParams,
                requires_approval=True,
            )
        )
        self.register(
            ToolDefinition(
                name="support_ticket_create",
                description="Create a new high-priority customer support ticket.",
                category=ToolCategory.STATE_CHANGING,
                param_model=SupportTicketCreateParams,
                requires_approval=True,
            )
        )
        self.register(
            ToolDefinition(
                name="ticket_status_lookup",
                description="Look up status and priority of an existing support ticket.",
                category=ToolCategory.READ_ONLY,
                param_model=TicketStatusLookupParams,
                requires_approval=False,
            )
        )
        self.register(
            ToolDefinition(
                name="operation_status_check",
                description="Check execution outcome and audit status of an asynchronous operation ID.",
                category=ToolCategory.READ_ONLY,
                param_model=OperationStatusCheckParams,
                requires_approval=False,
            )
        )

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def validate_params(self, tool_name: str, raw_params: Dict[str, Any]) -> BaseModel:
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unauthorized or unknown tool: {tool_name}")
        return tool.param_model(**raw_params)
