# Enterprise Client Deployment Guide: Sentinel AI Fabric

## 1. Deployment Topology & Environments

Sentinel Enterprise AI Fabric supports two primary production deployment architectures:
1. **Air-Gapped Private VPC on Kubernetes (EKS / GKE / OpenShift)** (Recommended)
2. **On-Premise Virtual Machines via Docker Compose**

---

## 2. Docker Compose Deployment (Local Integration / On-Premise)

### Step 1: Clone Repository & Create Data Directory
```bash
git clone git@github-rajeshwari:rajeshwari229080/Datheon_Forward_Deployed_Engineering_Internship.git
cd Datheon_Forward_Deployed_Engineering_Internship
mkdir -p data/chroma data/audit
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and configure appropriate variables:
```bash
cp .env.example .env
chmod 600 .env
```

### Step 3: Launch Service Containers
```bash
docker compose up -d --build
```

### Step 4: Verify Service Health
```bash
docker compose ps
docker compose logs -f
curl -f http://localhost:8000/health/ready || exit 1
```

---

## 3. Kubernetes Production Hardening Guide

When deploying to a client Kubernetes cluster, apply the following controls:

### Security Context & Pod Security Standards
Ensure pods comply with the `Restricted` Pod Security Standard:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinel-fabric
  namespace: sentinel-prod
spec:
  replicas: 3
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: sentinel-api
          image: sentinel-enterprise-fabric:1.0.0
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: persistent-data
              mountPath: /app/data
            - name: tmp-dir
              mountPath: /tmp
```

### Persistent Volume Claims (PVC)
ChromaDB requires high-IOPS persistent storage (e.g. AWS `gp3`, Azure `Premium_LRS`, or local NVMe storage classes).

---

## 4. Key Management & Secrets Integration

Never commit production secrets into code or plain `.env` files.
- **HMAC Governance Secret (`AGENT_APPROVAL_SECRET`)**: Inject via Kubernetes External Secrets Operator linked to AWS Secrets Manager, Google Secret Manager, or HashiCorp Vault.
- **Encryption at Rest**: Enable volume-level encryption (e.g. KMS CMK encryption on EBS / Persistent Disks).

---

## 5. Backup, Disaster Recovery & Retention

1. **ChromaDB Backups**:
   - Schedule daily filesystem snapshots of `/app/data/chroma`.
   - Maintain a 30-day retention window with cross-region replication for disaster recovery.
2. **Audit Event Log Retention**:
   - Stream `/app/data/audit/audit_events.jsonl` to an immutable, write-once-read-many (WORM) storage bucket (e.g., AWS S3 Object Lock in Compliance Mode) or enterprise SIEM (Splunk, Elastic, Datadog).
   - Retain audit records for a minimum of 7 years in regulated environments.
