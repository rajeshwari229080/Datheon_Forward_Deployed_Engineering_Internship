"""Test configuration and reusable fixtures."""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure src is in python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sentinel.api.app import create_app
from sentinel.core.config import Settings
from sentinel.core.models import ClearanceLevel, Role, UserIdentity


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("test_data")
    return Settings(
        env="testing",
        data_dir=data_dir,
        chroma_persist_dir=data_dir / "chroma",
        audit_log_path=data_dir / "audit.jsonl",
        embedding_provider="mock",
        llm_provider="mock",
    )


@pytest.fixture(scope="session")
def client(test_settings):
    app = create_app(test_settings)
    return TestClient(app)


@pytest.fixture
def tenant_alpha_user():
    return UserIdentity(
        user_id="usr-alpha-101",
        tenant_id="tenant-alpha",
        username="alice",
        department="finance",
        role=Role.OPERATOR,
        clearance=ClearanceLevel.SECRET,
        allowed_departments=["finance"],
    )


@pytest.fixture
def tenant_beta_user():
    return UserIdentity(
        user_id="usr-beta-202",
        tenant_id="tenant-beta",
        username="bob",
        department="engineering",
        role=Role.ANALYST,
        clearance=ClearanceLevel.CONFIDENTIAL,
        allowed_departments=["engineering"],
    )


@pytest.fixture
def unclassified_user():
    return UserIdentity(
        user_id="usr-public-001",
        tenant_id="tenant-alpha",
        username="charlie",
        department="finance",
        role=Role.VIEWER,
        clearance=ClearanceLevel.PUBLIC,
        allowed_departments=["finance"],
    )
