"""Security boundaries and authorization policy resolution outside of the LLM."""

from typing import Optional
from fastapi import Header, HTTPException, status
from sentinel.core.models import ClearanceLevel, Role, UserIdentity


class SecurityViolationError(Exception):
    """Raised when an unauthorized access or tenant boundary breach is attempted."""
    pass


class PolicyEngine:
    """Enforces zero-trust ABAC and RBAC policies outside the LLM reasoning loop."""

    @staticmethod
    def can_access_document(
        user: UserIdentity,
        document_tenant_id: str,
        document_department: str,
        document_clearance: ClearanceLevel,
    ) -> bool:
        """Evaluate if user is authorized to view a specific document or chunk.

        Rules:
        1. Tenant isolation: Must match user tenant ID exactly. Cross-tenant access is unconditionally denied.
        2. Clearance level: User's clearance rank must be >= document's clearance rank.
        3. Department isolation: If document has a specific department, user must belong to that department
           or have it listed in allowed_departments, or hold an ADMIN role.
        """
        # Rule 1: Tenant Boundary
        if user.tenant_id != document_tenant_id:
            return False

        # Rule 2: Clearance Level
        if not user.clearance.satisfies(document_clearance):
            return False

        # Rule 3: Department Boundary
        if document_department and document_department.lower() != "all":
            if user.role != Role.ADMIN:
                dept_match = (
                    user.department.lower() == document_department.lower()
                    or document_department.lower() in [d.lower() for d in user.allowed_departments]
                )
                if not dept_match:
                    return False

        return True

    @staticmethod
    def can_execute_action(user: UserIdentity, is_write: bool, required_role: Role = Role.OPERATOR) -> bool:
        """Check if user has adequate role to perform an action."""
        role_ranks = {
            Role.VIEWER: 1,
            Role.ANALYST: 2,
            Role.OPERATOR: 3,
            Role.ADMIN: 4,
        }
        user_rank = role_ranks.get(user.role, 1)
        required_rank = role_ranks.get(required_role, 3)

        if is_write and user_rank < required_rank:
            return False
        return True


def resolve_user_identity(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_username: Optional[str] = Header(None, alias="X-Username"),
    x_department: Optional[str] = Header(None, alias="X-Department"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
    x_clearance: Optional[str] = Header(None, alias="X-Clearance"),
) -> UserIdentity:
    """Extract and validate user identity from trusted server-gateway headers."""
    tenant_id = x_tenant_id or "default-tenant"
    user_id = x_user_id or "usr-default"
    username = x_username or "default_user"
    department = x_department or "general"

    # Validate role
    try:
        role = Role(x_role.lower()) if x_role else Role.VIEWER
    except ValueError:
        role = Role.VIEWER

    # Validate clearance
    try:
        clearance = ClearanceLevel(x_clearance.lower()) if x_clearance else ClearanceLevel.INTERNAL
    except ValueError:
        clearance = ClearanceLevel.INTERNAL

    return UserIdentity(
        user_id=user_id,
        tenant_id=tenant_id,
        username=username,
        department=department,
        role=role,
        clearance=clearance,
        allowed_departments=[department],
    )
