"""Mock stateful ERP/CRM transactional backend with idempotency and isolation."""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    sku: str
    name: str
    quantity: int
    warehouse: str
    unit_price: float


class CustomerRecord(BaseModel):
    customer_id: str
    name: str
    email: str
    tier: str
    credit_limit: float


class LeadRecord(BaseModel):
    lead_id: str
    contact_name: str
    company: str
    status: str
    updated_at: float = Field(default_factory=time.time)


class SupportTicket(BaseModel):
    ticket_id: str
    customer_id: str
    subject: str
    priority: str
    status: str = "OPEN"
    created_at: float = Field(default_factory=time.time)


class MockERPBackend:
    """Stateful, thread-safe in-memory ERP and CRM simulation with tenant isolation."""

    def __init__(self):
        # Tenant partitioned storage: tenant_id -> dict
        self._inventory: Dict[str, Dict[str, InventoryItem]] = {}
        self._customers: Dict[str, Dict[str, CustomerRecord]] = {}
        self._leads: Dict[str, Dict[str, LeadRecord]] = {}
        self._tickets: Dict[str, Dict[str, SupportTicket]] = {}
        self._operations: Dict[str, Dict[str, Any]] = {}
        self._idempotency_registry: Dict[str, Dict[str, Any]] = {}

        # Pre-seed default data for tests
        self._seed_default_tenant("tenant-alpha")
        self._seed_default_tenant("default-tenant")

    def _seed_default_tenant(self, tenant_id: str) -> None:
        self._inventory[tenant_id] = {
            "SKU-1001": InventoryItem(sku="SKU-1001", name="High-Performance Server Blade", quantity=45, warehouse="US-EAST-1", unit_price=4500.0),
            "SKU-1002": InventoryItem(sku="SKU-1002", name="100Gbps Optical Transceiver", quantity=120, warehouse="US-WEST-2", unit_price=250.0),
        }
        self._customers[tenant_id] = {
            "CUST-001": CustomerRecord(customer_id="CUST-001", name="Acme Aerospace", email="procurement@acme.example.com", tier="ENTERPRISE", credit_limit=500000.0),
            "CUST-002": CustomerRecord(customer_id="CUST-002", name="Globex Cyber", email="admin@globex.example.com", tier="STANDARD", credit_limit=50000.0),
        }
        self._leads[tenant_id] = {
            "LEAD-501": LeadRecord(lead_id="LEAD-501", contact_name="Sarah Connor", company="Cyberdyne", status="NEW"),
        }
        self._tickets[tenant_id] = {
            "TCK-9001": SupportTicket(ticket_id="TCK-9001", customer_id="CUST-001", subject="Latency spike on VPC gateway", priority="HIGH", status="OPEN"),
        }
        self._operations[tenant_id] = {}
        self._idempotency_registry[tenant_id] = {}

    def lookup_inventory(self, tenant_id: str, sku: str) -> Optional[Dict[str, Any]]:
        tenant_inv = self._inventory.get(tenant_id, {})
        item = tenant_inv.get(sku)
        return item.model_dump() if item else None

    def lookup_customer(self, tenant_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        tenant_cust = self._customers.get(tenant_id, {})
        cust = tenant_cust.get(customer_id)
        return cust.model_dump() if cust else None

    def update_lead_status(
        self,
        tenant_id: str,
        lead_id: str,
        new_status: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        tenant_leads = self._leads.setdefault(tenant_id, {})
        idemp_reg = self._idempotency_registry.setdefault(tenant_id, {})

        if idempotency_key and idempotency_key in idemp_reg:
            return idemp_reg[idempotency_key]

        lead = tenant_leads.get(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found for tenant {tenant_id}")

        lead.status = new_status
        lead.updated_at = time.time()
        result = {"success": True, "lead_id": lead_id, "status": new_status, "updated_at": lead.updated_at}

        if idempotency_key:
            idemp_reg[idempotency_key] = result
        return result

    def create_support_ticket(
        self,
        tenant_id: str,
        customer_id: str,
        subject: str,
        priority: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        tenant_tickets = self._tickets.setdefault(tenant_id, {})
        idemp_reg = self._idempotency_registry.setdefault(tenant_id, {})

        if idempotency_key and idempotency_key in idemp_reg:
            return idemp_reg[idempotency_key]

        # Verify customer exists in this tenant
        if not self.lookup_customer(tenant_id, customer_id):
            raise ValueError(f"Customer {customer_id} does not exist in tenant {tenant_id}")

        ticket_id = f"TCK-{len(tenant_tickets) + 9002}"
        ticket = SupportTicket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            subject=subject,
            priority=priority,
            status="OPEN",
        )
        tenant_tickets[ticket_id] = ticket
        result = {"success": True, "ticket_id": ticket_id, "status": "OPEN", "priority": priority}

        if idempotency_key:
            idemp_reg[idempotency_key] = result
        return result

    def lookup_ticket_status(self, tenant_id: str, ticket_id: str) -> Optional[Dict[str, Any]]:
        tenant_tickets = self._tickets.get(tenant_id, {})
        ticket = tenant_tickets.get(ticket_id)
        return ticket.model_dump() if ticket else None

    def record_operation(self, tenant_id: str, operation_id: str, details: Dict[str, Any]) -> None:
        tenant_ops = self._operations.setdefault(tenant_id, {})
        tenant_ops[operation_id] = details

    def get_operation_status(self, tenant_id: str, operation_id: str) -> Optional[Dict[str, Any]]:
        tenant_ops = self._operations.get(tenant_id, {})
        return tenant_ops.get(operation_id)
