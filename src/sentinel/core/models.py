"""Core domain models for identity, access control, and metadata provenance."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClearanceLevel(str, Enum):
    """Hierarchical security clearance levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

    @property
    def level_rank(self) -> int:
        rank_map = {
            ClearanceLevel.PUBLIC: 0,
            ClearanceLevel.INTERNAL: 1,
            ClearanceLevel.CONFIDENTIAL: 2,
            ClearanceLevel.SECRET: 3,
            ClearanceLevel.TOP_SECRET: 4,
        }
        return rank_map[self]

    def satisfies(self, required: "ClearanceLevel") -> bool:
        """Returns True if this clearance rank is greater than or equal to required."""
        return self.level_rank >= required.level_rank


class Role(str, Enum):
    """Platform roles for RBAC enforcement."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    OPERATOR = "operator"
    ADMIN = "admin"


class UserIdentity(BaseModel):
    """Authenticated user identity extracted from server-validated context."""
    user_id: str
    tenant_id: str
    username: str
    department: str
    role: Role = Role.VIEWER
    clearance: ClearanceLevel = ClearanceLevel.INTERNAL
    allowed_departments: List[str] = Field(default_factory=list)


class TenantPolicy(BaseModel):
    """Tenant-specific data isolation and compliance rules."""
    tenant_id: str
    name: str
    enforce_strict_department_boundary: bool = True
    allowed_clearance_max: ClearanceLevel = ClearanceLevel.TOP_SECRET
    require_human_approval_for_writes: bool = True
