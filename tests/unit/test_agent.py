"""Unit tests for Workstream C: Governed Agent, Tool Schemas, Approvals, and Idempotency."""

import time
import pytest
from sentinel.agent.approvals import ApprovalGate
from sentinel.agent.engine import AgentEngine
from sentinel.agent.mock_backend import MockERPBackend
from sentinel.agent.tools import ToolRegistry
from sentinel.core.models import ClearanceLevel, Role, UserIdentity


def test_mock_backend_inventory_lookup():
    backend = MockERPBackend()
    item = backend.lookup_inventory(tenant_id="tenant-alpha", sku="SKU-1001")
    assert item is not None
    assert item["sku"] == "SKU-1001"
    assert item["quantity"] == 45


def test_mock_backend_idempotent_ticket_create():
    backend = MockERPBackend()
    key = "idem-ticket-123"
    r1 = backend.create_support_ticket(
        tenant_id="tenant-alpha", customer_id="CUST-001", subject="VPN Tunnel down", priority="CRITICAL", idempotency_key=key
    )
    r2 = backend.create_support_ticket(
        tenant_id="tenant-alpha", customer_id="CUST-001", subject="VPN Tunnel down", priority="CRITICAL", idempotency_key=key
    )
    assert r1["ticket_id"] == r2["ticket_id"]


def test_tool_registry_validation():
    registry = ToolRegistry()
    valid = registry.validate_params("inventory_lookup", {"sku": "SKU-9999"})
    assert valid.sku == "SKU-9999"

    with pytest.raises(Exception):
        registry.validate_params("inventory_lookup", {})  # missing sku


def test_approval_gate_hmac_and_replay_protection(tenant_alpha_user):
    gate = ApprovalGate()
    req = gate.create_approval_request(
        tenant_id="tenant-alpha",
        user=tenant_alpha_user,
        tool_name="lead_status_update",
        arguments={"lead_id": "LEAD-501", "new_status": "QUALIFIED"},
    )
    op_id = req["operation_id"]
    token = req["approval_token"]

    # First consumption -> Success
    consumed = gate.verify_and_consume(op_id, token, tenant_alpha_user)
    assert consumed.is_executed is True

    # Second consumption -> Replay Denied
    with pytest.raises(ValueError, match="already been executed"):
        gate.verify_and_consume(op_id, token, tenant_alpha_user)


def test_agent_engine_requires_approval_for_writes(tenant_alpha_user):
    engine = AgentEngine()
    # Read-only operation should execute directly
    read_res = engine.execute_action(
        user=tenant_alpha_user,
        tool_name="inventory_lookup",
        parameters={"sku": "SKU-1001"},
    )
    assert read_res.success is True
    assert read_res.status == "COMPLETED"
    assert read_res.action_trace.approval_status == "NOT_REQUIRED"

    # State-changing write should be halted by approval gate
    write_res = engine.execute_action(
        user=tenant_alpha_user,
        tool_name="lead_status_update",
        parameters={"lead_id": "LEAD-501", "new_status": "QUALIFIED"},
    )
    assert write_res.success is True
    assert write_res.status == "APPROVAL_REQUIRED"
    assert "operation_id" in write_res.approval_details
