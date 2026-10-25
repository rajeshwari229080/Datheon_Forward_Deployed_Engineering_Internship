"""Unit tests for Workstream D: REST API endpoints and HTTP interfaces."""

import io
from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient):
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "alive"

    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"


def test_metrics_endpoint(client: TestClient):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"sentinel_http_requests_total" in r.content or b"sentinel_system_healthy" in r.content


def test_document_ingestion_api(client: TestClient):
    csv_content = b"SKU,Name,Price\nSKU-500,Switch,999.00\n"
    files = [("files", ("products.csv", io.BytesIO(csv_content), "text/csv"))]
    headers = {
        "X-Tenant-ID": "tenant-alpha",
        "X-User-ID": "usr-01",
        "X-Department": "operations",
        "X-Role": "operator",
        "X-Clearance": "internal",
    }
    r = client.post("/api/v1/documents/ingest", files=files, headers=headers)
    assert r.status_code == 200
    manifest = r.json()
    assert manifest["processed_files"] == 1
    assert manifest["indexed_chunks"] >= 1


def test_rag_query_api(client: TestClient):
    headers = {
        "X-Tenant-ID": "tenant-alpha",
        "X-User-ID": "usr-01",
        "X-Department": "operations",
        "X-Role": "operator",
        "X-Clearance": "internal",
    }
    r = client.post("/api/v1/rag/query", json={"query": "Switch price"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "citations" in data


def test_agent_execution_and_approval_api(client: TestClient):
    headers = {
        "X-Tenant-ID": "tenant-alpha",
        "X-User-ID": "usr-01",
        "X-Department": "operations",
        "X-Role": "operator",
        "X-Clearance": "internal",
    }

    # Step 1: Request state-changing action
    req_body = {
        "tool_name": "lead_status_update",
        "parameters": {"lead_id": "LEAD-501", "new_status": "CONVERTED"},
    }
    r1 = client.post("/api/v1/agent/execute", json=req_body, headers=headers)
    assert r1.status_code == 200
    res1 = r1.json()
    assert res1["status"] == "APPROVAL_REQUIRED"
    approval_details = res1["approval_details"]
    op_id = approval_details["operation_id"]
    token = approval_details["approval_token"]

    # Step 2: Submit approval token
    r2 = client.post(
        f"/api/v1/approvals/{op_id}",
        json={"approval_token": token},
        headers=headers,
    )
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["status"] == "COMPLETED"
    assert res2["data"]["status"] == "CONVERTED"
