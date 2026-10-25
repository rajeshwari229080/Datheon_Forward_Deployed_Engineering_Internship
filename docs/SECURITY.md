# Security Policy & Hardening Controls: Sentinel Enterprise AI Fabric

## 1. Security Architecture Principles

Sentinel Enterprise AI Fabric implements the following defense-in-depth security principles:

1. **Authorization Outside the Model**: Never rely on an LLM to decide whether a user is allowed to view a document. All authorization filtering occurs in Python before candidates are sent to the vector store or generation engine.
2. **Untrusted Data Isolation**: All retrieved content and uploaded files are treated as untrusted user input. Delimiters (`<source_evidence>`) prevent context leakage into instruction channels.
3. **Cryptographic Action Binding**: State-changing operations require explicit HMAC-SHA256 tokens bound to specific parameters and timestamps.
4. **Least Privilege**: Services run under unprivileged non-root users (`UID 10001`). File system writes are restricted to designated data directories.

---

## 2. Access Control Model

### Clearance Hierarchy
Clearance levels are strictly hierarchical:
- `PUBLIC` (Rank 0)
- `INTERNAL` (Rank 1)
- `CONFIDENTIAL` (Rank 2)
- `SECRET` (Rank 3)
- `TOP_SECRET` (Rank 4)

A user with clearance level `C_user` can only retrieve documents where `C_doc <= C_user`.

### Role-Based Access Control (RBAC)
- `VIEWER`: Read-only search and query capabilities.
- `ANALYST`: Querying, search, and analytical tool execution (`inventory_lookup`, `customer_lookup`).
- `OPERATOR`: Permitted to initiate state-changing tool operations (`lead_status_update`, `support_ticket_create`).
- `ADMIN`: Global administration, cross-department visibility, and audit inspection.

---

## 3. Sensitive Data Redaction & Logging Controls

The application uses an automated regex-based redaction engine on all log entries:
- **Authorization Tokens & API Keys**: `Authorization: Bearer ***REDACTED***`
- **Credit Card Numbers**: Formats matching `####-####-####-####` masked to `***CARD_REDACTED***`
- **Social Security Numbers**: Formats matching `###-##-####` masked to `***SSN_REDACTED***`

High-cardinality values (user emails, raw document texts, secret tokens) are strictly excluded from Prometheus metric labels to prevent cardinality exhaustion and metric-based information leaks.

---

## 4. Reporting Security Vulnerabilities

To report a vulnerability or security flaw, please contact the Sentinel Security Team:
- **Email**: `security@sentinel.internal`
- **PGP Key**: Available upon request
- **Response SLA**: Initial triage within 24 business hours; critical patch delivery within 72 hours.
