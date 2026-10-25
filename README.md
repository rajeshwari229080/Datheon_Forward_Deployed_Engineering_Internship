# Sentinel Enterprise AI Fabric

> **Risk-Driven Multi-Tenant RAG, Governed Autonomous Agent & Vector ETL Platform**

Sentinel Enterprise AI Fabric is a production-grade, zero-trust AI application platform engineered to transform fragmented corporate information into authorized knowledge and audited transactional actions. Designed for restricted client environments, it prioritizes data isolation, provenance tracking, operational simplicity, and verifiable evidence over ungrounded demonstrations.

---

## Core Platform Capabilities

1. **Legacy Data Ingestion and Vector ETL (Workstream A)**
   - Resilient ingestion pipeline for PDF, CSV, and Markdown documents.
   - Preserves exact page numbers (PDF), row identifiers (CSV), and heading hierarchies (Markdown).
   - Structure-aware and semantic chunking with SHA-256 cryptographic fingerprints.
   - Deduplication by source hash; update and deletion propagation.
   - ChromaDB persistent vector store with cosine distance and hybrid BM25 lexical index.

2. **Adversarially Tested Multi-Tenant RAG (Workstream B)**
   - Strict authorization boundary enforced outside the LLM.
   - Zero-trust RBAC and clearance-based access control (Public, Internal, Confidential, Secret, Top Secret).
   - Query rewriting neutralizing direct and indirect prompt injection attempts.
   - Hybrid retrieval combining dense vector similarity with sparse BM25 via Reciprocal Rank Fusion (RRF).
   - Cross-encoder reranking with grounding threshold enforcement.
   - Verifiable page-level citations and evidence-aware abstention on unsupported queries.

3. **Governed Autonomous ERP/CRM Agent (Workstream C)**
   - Constrained tool registry: `inventory_lookup`, `customer_lookup`, `lead_status_update`, `support_ticket_create`, `ticket_status_lookup`, `operation_status_check`.
   - Strict separation of read-only operations from sensitive state-changing writes.
   - Two-phase cryptographic approval gate using HMAC-SHA256 signatures with expiry and single-use replay protection.
   - Idempotency key tracking across retryable transactions.
   - Append-only JSONL audit event logging with correlation ID propagation.

4. **Hardened Deployment & Observability (Workstream D)**
   - FastAPI gateway with liveness, readiness, and Prometheus metrics exposition (`/metrics`).
   - Multi-stage Docker container execution under an unprivileged non-root user (`UID 10001`).
   - Rate limiting, request size limits, and sensitive data redaction in structured logs.
   - Fully offline capable: operates without paid third-party API dependencies.

---

## Rapid Local Start

### Prerequisites
- Python 3.12+
- Docker and Docker Compose (optional for containerized execution)

### 1. Installation
```bash
git clone git@github-rajeshwari:rajeshwari229080/Datheon_Forward_Deployed_Engineering_Internship.git
cd Datheon_Forward_Deployed_Engineering_Internship
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Service Locally
```bash
uvicorn sentinel.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Verify service health:
```bash
curl -s http://localhost:8000/health/live
curl -s http://localhost:8000/health/ready
curl -s http://localhost:8000/metrics
```

### 3. Run Automated Tests
```bash
# Run unit tests
python -m pytest tests/unit -v

# Run 10-gate adversarial regression security suite
python -m pytest tests/adversarial -v
```

### 4. Run Reproducible Benchmark Harness
```bash
python scripts/run_benchmarks.py
```

### 5. Run with Docker Compose
```bash
docker compose up --build -d
```

---

## Repository Architecture Map

```
.
├── Dockerfile                   # Hardened multi-stage non-root container build
├── docker-compose.yml           # Local integration deployment orchestration
├── pyproject.toml               # Package dependencies and tool settings
├── requirements.txt             # Pinned production requirements
├── src/
│   └── sentinel/
│       ├── core/                # Configuration, logging, models, and security boundary
│       │   ├── config.py        # Pydantic BaseSettings with env validation
│       │   ├── logging.py       # Structured JSON logger with correlation IDs & redaction
│       │   ├── models.py        # Tenant, User, Clearance, and Role schemas
│       │   └── security.py      # Zero-trust ABAC/RBAC authorization engine
│       ├── etl/                 # Document ingestion pipeline & extractors
│       │   ├── extractors/      # Format-specific extractors (PDF, CSV, Markdown)
│       │   ├── chunker.py       # Structure-aware chunking with cryptographic hashing
│       │   ├── pipeline.py      # 9-stage ETL orchestrator with deduplication
│       │   └── schemas.py       # Data contracts and ingestion manifests
│       ├── vector/              # Vector storage, embeddings, hybrid search & reranking
│       │   ├── embeddings.py    # Local deterministic & Ollama embedding adapters
│       │   ├── chroma.py        # Persistent ChromaDB vector store with metadata filtering
│       │   ├── bm25.py          # In-memory Okapi BM25 sparse index
│       │   ├── hybrid.py        # Reciprocal Rank Fusion (RRF) search engine
│       │   └── reranker.py      # Cross-encoder joint scoring and threshold filter
│       ├── rag/                 # Multi-tenant RAG orchestration
│       │   ├── pipeline.py      # Query rewriting and candidate retrieval
│       │   ├── context.py       # Deduplication and token-budget manager
│       │   ├── citations.py     # Provenance resolver & grounding validator
│       │   └── generator.py     # Grounded synthesis and safe abstention
│       ├── agent/               # Governed autonomous ERP/CRM agent
│       │   ├── mock_backend.py  # Stateful ERP/CRM transactional simulation
│       │   ├── tools.py         # Typed tool registry & Pydantic validators
│       │   ├── approvals.py     # Two-phase cryptographic approval gate
│       │   ├── audit.py         # Append-only JSONL audit event logger
│       │   └── engine.py        # Execution coordinator with retries & action traces
│       ├── telemetry/           # Prometheus metrics definitions & exposition
│       └── api/                 # FastAPI routes and middleware
│           ├── app.py           # Application factory & security middleware
│           └── routes/          # REST endpoints (health, documents, rag, agent)
├── tests/
│   ├── unit/                    # Workstreams A, B, C, D unit tests
│   └── adversarial/             # 10-gate adversarial regression test suite
└── scripts/
    └── run_benchmarks.py        # Benchmark harness for throughput, latency, recall
```

---

## Client Documentation Package
- [ARCHITECTURE.md](ARCHITECTURE.md) — System boundaries, sequence diagrams, design decisions.
- [THREAT_MODEL.md](THREAT_MODEL.md) — STRIDE threat modeling, trust boundaries, mitigations.
- [SECURITY.md](SECURITY.md) — Authorization rules, prompt injection defense, audit controls.
- [API_GUIDE.md](API_GUIDE.md) — API contract reference with sample requests and responses.
- [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md) — VPC deployment, Kubernetes guidelines, secrets management.
- [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) — Measured throughput, latency distributions, and recall metrics.
- [TEST_REPORT.md](TEST_REPORT.md) — Test results for unit and adversarial test suites.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Diagnostic procedures, error codes, and operational recovery.
- [.env.example](.env.example) — Configuration reference with safe default values.
