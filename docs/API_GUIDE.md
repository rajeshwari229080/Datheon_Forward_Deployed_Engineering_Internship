# API Reference Guide: Sentinel Enterprise AI Fabric

All API endpoints are hosted under `/api/v1` and require authenticated identity headers.

---

## 1. Authentication Headers

Every request to `/api/v1/*` must include standard server-gateway identity headers:

| Header Name | Type | Required | Description |
|:---|:---|:---|:---|
| `X-Tenant-ID` | String | Yes | Unique tenant identifier (e.g., `tenant-alpha`) |
| `X-User-ID` | String | Yes | Unique user identifier (e.g., `usr-101`) |
| `X-Role` | String | No | User role (`viewer`, `analyst`, `operator`, `admin`) |
| `X-Clearance` | String | No | Security clearance (`public`, `internal`, `confidential`, `secret`, `top_secret`) |
| `X-Department` | String | No | User department (e.g., `engineering`, `finance`, `operations`) |
| `X-Correlation-ID` | String | No | Client trace correlation ID (auto-generated if omitted) |

---

## 2. Ingestion Endpoints

### `POST /api/v1/documents/ingest`
Uploads and indexes documents with structural extraction and provenance tracking.

**Request**: Multipart Form Data
- `files`: One or more files (`.pdf`, `.csv`, `.md`)
- `department`: (Optional) Target department name
- `clearance`: (Optional) Document security clearance level

**Sample Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/ingest" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -H "X-Role: operator" \
  -H "X-Clearance: internal" \
  -F "files=@annual_report.pdf" \
  -F "department=finance" \
  -F "clearance=internal"
```

**Sample Response (200 OK)**:
```json
{
  "job_id": "job-7a8b9c0d1e",
  "tenant_id": "tenant-alpha",
  "processed_files": 1,
  "skipped_duplicates": 0,
  "failed_files": 0,
  "indexed_chunks": 14,
  "errors": [],
  "completed_at": "2026-10-25T10:30:00Z"
}
```

### `GET /api/v1/documents/jobs/{job_id}`
Checks the execution status of an ingestion job.

---

## 3. Search & RAG Endpoints

### `POST /api/v1/search`
Performs authorized hybrid vector and lexical retrieval.

**Sample Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -d '{"query": "quarterly revenue metrics", "top_k": 5}'
```

### `POST /api/v1/rag/query`
Executes grounded question answering with verified citations.

**Sample Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -H "X-Clearance: secret" \
  -d '{"query": "What are our compliance guidelines for cloud storage?"}'
```

**Sample Response (200 OK)**:
```json
{
  "query": "What are our compliance guidelines for cloud storage?",
  "rewritten_query": "compliance guidelines cloud storage",
  "answer": "Based on the authorized enterprise documentation, cloud storage must enforce AES-256 encryption at rest...",
  "citations": [
    {
      "chunk_id": "doc_123_chk_0_a1b2c3d4",
      "document_id": "doc_123",
      "filename": "security_standards.md",
      "page_number": null,
      "row_id": null,
      "heading_path": "Cloud Security > Storage",
      "snippet": "All multi-tenant storage buckets must enforce AES-256...",
      "source_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "verified": true
    }
  ],
  "abstained": false,
  "evidence_chunk_count": 1,
  "timings_ms": {
    "rewrite_ms": 1.2,
    "retrieval_ms": 14.5,
    "rerank_ms": 3.8,
    "generation_ms": 42.1
  },
  "tenant_id": "tenant-alpha"
}
```

---

## 4. Governed Autonomous Agent Endpoints

### `POST /api/v1/agent/execute`
Initiates a governed tool operation.

**Read-Only Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/agent/execute" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -d '{
    "tool_name": "inventory_lookup",
    "parameters": {"sku": "SKU-1001"}
  }'
```

**State-Changing Write Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/agent/execute" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -H "X-Role: operator" \
  -d '{
    "tool_name": "lead_status_update",
    "parameters": {"lead_id": "LEAD-501", "new_status": "QUALIFIED"}
  }'
```

**Approval Required Response (200 OK)**:
```json
{
  "success": true,
  "status": "APPROVAL_REQUIRED",
  "action_trace": {
    "requested_action": "lead_status_update",
    "validation_outcome": "VALIDATED",
    "approval_status": "APPROVAL_REQUIRED: Operation op_1792925515_dec50371",
    "tool_invocation": "PENDING_APPROVAL",
    "observed_result": null,
    "final_status": "PENDING_APPROVAL",
    "execution_time_ms": 2.4
  },
  "approval_details": {
    "status": "APPROVAL_REQUIRED",
    "operation_id": "op_1792925515_dec50371",
    "tool_name": "lead_status_update",
    "approval_token": "a1b2c3d4e5f6...7890",
    "expires_at": 1792926415.0
  }
}
```

### `POST /api/v1/approvals/{operation_id}`
Submits a cryptographic approval token to execute a pending state change.

```bash
curl -X POST "http://localhost:8000/api/v1/approvals/op_1792925515_dec50371" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-alpha" \
  -H "X-User-ID: usr-101" \
  -H "X-Role: operator" \
  -d '{"approval_token": "a1b2c3d4e5f6...7890"}'
```

---

## 5. System Health & Observability Endpoints

- `GET /health/live` — 200 OK service liveness probe.
- `GET /health/ready` — 200 OK dependency readiness probe.
- `GET /metrics` — Prometheus metrics exposition in OpenMetrics text format.
