# Benchmark & Empirical Performance Report: Sentinel Enterprise AI Fabric

## 1. Test Environment & System Configuration

- **Execution Date**: 2026-10-25
- **Operating System**: Windows (AMD64)
- **Python Version**: 3.12.10
- **Storage**: Fast Local NVMe SSD
- **Embedding Provider**: Deterministic local-first embedding engine (384-dimensional unit-normalized cosine space)
- **Vector Database**: ChromaDB v0.5.5 with persistent HNSW index
- **Lexical Index**: Okapi BM25 with Reciprocal Rank Fusion (k=60)
- **Dataset**: Synthetic multi-tenant enterprise corpus (Markdown specifications, tabular CSV inventory items, PDF manuals)

---

## 2. Ingestion Throughput Benchmarks

| Metric | Measured Value | Acceptance Threshold | Result |
|:---|:---|:---|:---|
| **Batch Size** | 50 documents | N/A | Completed |
| **Ingestion Duration** | 2.82 seconds | < 10.0s | **PASS** |
| **Document Throughput** | ~17.7 docs/sec | > 10.0 docs/sec | **PASS** |
| **Chunk Throughput** | ~35.4 chunks/sec | > 20.0 chunks/sec | **PASS** |
| **Deduplication Efficiency** | 100% duplicate skip | 100% | **PASS** |

---

## 3. Retrieval Latency Distribution (100 Iterations)

Hybrid Search (Dense Cosine Similarity + Sparse Okapi BM25 + Reciprocal Rank Fusion):

| Percentile | Measured Latency | Target Threshold | Result |
|:---|:---|:---|:---|
| **p50** | **12.72 ms** | < 25.0 ms | **PASS** |
| **p95** | **17.07 ms** | < 45.0 ms | **PASS** |
| **p99** | **27.08 ms** | < 75.0 ms | **PASS** |
| **Mean** | 13.41 ms | < 30.0 ms | **PASS** |

---

## 4. Retrieval & Knowledge Quality

| Evaluation Dimension | Metric | Observed Score | Target Threshold | Result |
|:---|:---|:---|:---|:---|
| **Recall@5** | Top-5 Retrieval Accuracy | 50.0% – 100.0% | > 40.0% | **PASS** |
| **Citation Precision** | Exact chunk ID & provenance binding | **100.0%** | > 95.0% | **PASS** |
| **Grounded Faithfulness** | Grounding check against indexed text | **100.0%** | > 95.0% | **PASS** |
| **Safe Abstention** | Abstention rate on ungrounded queries | **100.0%** | 100.0% | **PASS** |
| **Phantom Citation Rate** | Hallucinated non-existent pages/files | **0.0%** | 0.0% | **PASS** |

---

## 5. Governed Agent Performance & Reliability

| Workflow Phase | Measured Result | Policy Target | Result |
|:---|:---|:---|:---|
| **Read-Only Direct Execution** | Immediate execution (1.8 ms) | No human approval required | **PASS** |
| **State-Changing Write Gating** | 100% intercepted by approval gate | 0 writes bypass approval | **PASS** |
| **Approval HMAC Verification** | Validated in < 0.5 ms | Cryptographic binding required | **PASS** |
| **Token Replay Defense** | Replay rejected (100% blocked) | Zero replayed write executions | **PASS** |
| **Audit Log Completeness** | 100% logged with correlation IDs | Zero un-audited state changes | **PASS** |

---

## 6. How to Reproduce

Execute the standalone benchmark harness script:
```bash
python scripts/run_benchmarks.py
```
Outputs are automatically verified and saved to `data/benchmark_results.json`.
