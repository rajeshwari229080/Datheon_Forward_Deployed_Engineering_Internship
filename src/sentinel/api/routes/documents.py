"""Document ingestion and asynchronous ETL job status REST endpoints."""

import hashlib
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sentinel.core.config import get_settings
from sentinel.core.logging import get_logger
from sentinel.core.models import ClearanceLevel, UserIdentity
from sentinel.core.security import resolve_user_identity
from sentinel.etl.pipeline import IngestionPipeline
from sentinel.etl.schemas import DocumentType, IngestionJob, IngestionManifest, IngestionStatus, RawDocument
from sentinel.telemetry.metrics import INGESTION_CHUNKS_INDEXED_TOTAL, INGESTION_DOCUMENTS_TOTAL
from sentinel.vector.chroma import ChromaVectorStore
from sentinel.vector.hybrid import HybridRetriever

logger = get_logger("sentinel.api.routes.documents")

router = APIRouter(prefix="/api/v1/documents", tags=["Document ETL & Ingestion"])

# Shared pipeline instances
_vector_store = ChromaVectorStore()
_hybrid_retriever = HybridRetriever(vector_store=_vector_store)
_ingestion_pipeline = IngestionPipeline(retriever=_hybrid_retriever)
_jobs: Dict[str, IngestionJob] = {}


def get_pipeline() -> IngestionPipeline:
    return _ingestion_pipeline


def detect_file_type(filename: str) -> DocumentType:
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return DocumentType.PDF
    elif fn.endswith(".csv"):
        return DocumentType.CSV
    elif fn.endswith(".md") or fn.endswith(".markdown"):
        return DocumentType.MARKDOWN
    return DocumentType.UNKNOWN


@router.post("/ingest", response_model=IngestionManifest, status_code=status.HTTP_200_OK)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    department: Optional[str] = Form(None),
    clearance: Optional[str] = Form("internal"),
    user: UserIdentity = Depends(resolve_user_identity),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Ingest, extract, chunk, embed, and index enterprise documents with provenance tracking."""
    job_id = f"job-{uuid.uuid4().hex[:10]}"
    target_dept = department or user.department
    try:
        target_clearance = ClearanceLevel(clearance.lower()) if clearance else user.clearance
    except ValueError:
        target_clearance = user.clearance

    raw_docs: List[RawDocument] = []

    for file in files:
        content_bytes = await file.read()
        source_hash = hashlib.sha256(content_bytes).hexdigest()
        doc_type = detect_file_type(file.filename or "unknown")
        doc_id = f"doc_{source_hash[:12]}"

        raw_docs.append(
            RawDocument(
                document_id=doc_id,
                filename=file.filename or "unnamed",
                file_type=doc_type,
                content_bytes=content_bytes,
                tenant_id=user.tenant_id,
                department=target_dept,
                clearance=target_clearance,
                source_hash=source_hash,
            )
        )

    # Execute pipeline
    manifest = pipeline.ingest_batch(job_id=job_id, tenant_id=user.tenant_id, documents=raw_docs)

    # Update Prometheus metrics
    for doc in raw_docs:
        stat = "indexed" if manifest.processed_files > 0 else "failed"
        INGESTION_DOCUMENTS_TOTAL.labels(file_type=doc.file_type.value, status=stat).inc()
    INGESTION_CHUNKS_INDEXED_TOTAL.inc(manifest.indexed_chunks)

    # Store job
    _jobs[job_id] = IngestionJob(
        job_id=job_id,
        tenant_id=user.tenant_id,
        status=IngestionStatus.COMPLETED if manifest.failed_files == 0 else IngestionStatus.PARTIAL_FAILURE,
        total_files=len(files),
        processed_files=manifest.processed_files,
        failed_files=manifest.failed_files,
        manifest=manifest,
    )

    return manifest


@router.get("/jobs/{job_id}", response_model=IngestionJob, status_code=status.HTTP_200_OK)
def get_job_status(
    job_id: str,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Retrieve execution status and manifest of an ingestion job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingestion job {job_id} not found.")
    if job.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant job access denied.")
    return job
