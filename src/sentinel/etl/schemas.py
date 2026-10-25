"""Schemas and data models for document ingestion and vector ETL."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sentinel.core.models import ClearanceLevel


class DocumentType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class RawDocument(BaseModel):
    """Raw uploaded document with cryptographic hash and security metadata."""
    document_id: str
    filename: str
    file_type: DocumentType
    content_bytes: bytes
    tenant_id: str
    department: str
    clearance: ClearanceLevel = ClearanceLevel.INTERNAL
    document_date: Optional[str] = None
    source_hash: str
    parser_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExtractionItem(BaseModel):
    """Extracted atomic slice of a document with exact provenance."""
    text: str
    page_number: Optional[int] = None
    row_id: Optional[int] = None
    heading_hierarchy: List[str] = Field(default_factory=list)
    item_metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Normalized output from a document extractor."""
    document_id: str
    file_type: DocumentType
    items: List[ExtractionItem]
    parser_version: str
    source_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """Chunk prepared for embedding and vector indexing with full audit provenance."""
    chunk_id: str
    document_id: str
    filename: str
    tenant_id: str
    department: str
    clearance: ClearanceLevel
    text: str
    chunk_index: int
    page_number: Optional[int] = None
    row_id: Optional[int] = None
    heading_path: Optional[str] = None
    content_hash: str
    source_hash: str
    parser_version: str = "1.0.0"
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert chunk metadata to ChromaDB compatible flat dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "tenant_id": self.tenant_id,
            "department": self.department,
            "clearance": self.clearance.value,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number if self.page_number is not None else -1,
            "row_id": self.row_id if self.row_id is not None else -1,
            "heading_path": self.heading_path or "",
            "content_hash": self.content_hash,
            "source_hash": self.source_hash,
            "parser_version": self.parser_version,
            "indexed_at": self.indexed_at.isoformat(),
        }


class IngestionManifest(BaseModel):
    """Execution manifest reporting counts and errors for an ingestion run."""
    job_id: str
    tenant_id: str
    processed_files: int = 0
    skipped_duplicates: int = 0
    failed_files: int = 0
    indexed_chunks: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestionJob(BaseModel):
    """Tracking representation for asynchronous ingestion jobs."""
    job_id: str
    tenant_id: str
    status: IngestionStatus = IngestionStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    manifest: Optional[IngestionManifest] = None
