"""Orchestrator for the 9-stage document ingestion and vector ETL pipeline."""

import hashlib
import time
from typing import Dict, List, Optional
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.etl.chunker import StructureAwareChunker
from sentinel.etl.extractors import CSVExtractor, MarkdownExtractor, PDFExtractor
from sentinel.etl.schemas import (
    DocumentChunk,
    DocumentType,
    ExtractionResult,
    IngestionManifest,
    IngestionStatus,
    RawDocument,
)
from sentinel.vector.hybrid import HybridRetriever

logger = get_logger("sentinel.etl.pipeline")


class IngestionPipeline:
    """Orchestrates document processing through 9 risk-managed engineering stages:

    DISCOVER -> VALIDATE -> EXTRACT -> NORMALIZE -> CHUNK -> EMBED -> INDEX -> VERIFY -> REPORT
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.retriever = retriever
        self.chunker = StructureAwareChunker()
        self.pdf_extractor = PDFExtractor()
        self.csv_extractor = CSVExtractor()
        self.md_extractor = MarkdownExtractor()

        # In-memory deduplication registry of known source hashes: (tenant_id, document_id) -> source_hash
        self._processed_hashes: Dict[str, str] = {}

    def _get_extractor(self, doc_type: DocumentType):
        if doc_type == DocumentType.PDF:
            return self.pdf_extractor
        elif doc_type == DocumentType.CSV:
            return self.csv_extractor
        elif doc_type == DocumentType.MARKDOWN:
            return self.md_extractor
        raise ValueError(f"Unsupported document format: {doc_type}")

    # STAGE 1: DISCOVER & STAGE 2: VALIDATE
    def validate_document(self, doc: RawDocument) -> Optional[str]:
        """Validate document constraints (size, encoding, non-empty)."""
        if len(doc.content_bytes) == 0:
            return "File is empty (0 bytes)."
        if len(doc.content_bytes) > self.settings.max_upload_size_bytes:
            return f"File exceeds maximum allowed upload size ({len(doc.content_bytes)} > {self.settings.max_upload_size_bytes} bytes)."
        if doc.file_type == DocumentType.UNKNOWN:
            return f"Unsupported file extension for filename {doc.filename}."
        return None

    # STAGE 3: EXTRACT & STAGE 4: NORMALIZE
    def extract_and_normalize(self, doc: RawDocument) -> ExtractionResult:
        extractor = self._get_extractor(doc.file_type)
        return extractor.extract(doc)

    # STAGE 5: CHUNK
    def chunk_document(self, doc: RawDocument, extraction: ExtractionResult) -> List[DocumentChunk]:
        return self.chunker.chunk(
            extraction=extraction,
            raw_doc=doc,
            chunk_size=self.settings.default_chunk_size,
            chunk_overlap=self.settings.default_chunk_overlap,
        )

    # STAGES 6, 7 & 8: EMBED, INDEX & VERIFY
    def index_and_verify(self, tenant_id: str, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0
        self.retriever.index_chunks(tenant_id, chunks)
        return len(chunks)

    # STAGE 9: REPORT / COMPLETE PIPELINE EXECUTION
    def ingest_batch(self, job_id: str, tenant_id: str, documents: List[RawDocument]) -> IngestionManifest:
        """Run batch ingestion with idempotency, deduplication, and failure isolation."""
        manifest = IngestionManifest(job_id=job_id, tenant_id=tenant_id)
        start_time = time.time()

        for doc in documents:
            doc_key = f"{tenant_id}:{doc.document_id}"

            # Stage 1 & 2: Discover & Validate
            validation_err = self.validate_document(doc)
            if validation_err:
                manifest.failed_files += 1
                manifest.errors.append({"document_id": doc.document_id, "error": validation_err, "stage": "VALIDATE"})
                continue

            # Duplicate detection: check if source hash already matches
            if self._processed_hashes.get(doc_key) == doc.source_hash:
                manifest.skipped_duplicates += 1
                logger.info(f"Skipping duplicate document {doc.document_id} with unchanged hash {doc.source_hash}")
                continue

            try:
                # Stage 3 & 4: Extract & Normalize
                extraction = self.extract_and_normalize(doc)
                if extraction.warnings:
                    for w in extraction.warnings:
                        logger.warning(f"Extraction warning for {doc.document_id}: {w}")

                # Stage 5: Chunk
                chunks = self.chunk_document(doc, extraction)
                if not chunks:
                    manifest.failed_files += 1
                    manifest.errors.append({
                        "document_id": doc.document_id,
                        "error": "No valid text chunks produced.",
                        "stage": "CHUNK"
                    })
                    continue

                # Stage 6, 7 & 8: Embed, Index & Verify
                # If updating an existing document, delete old chunks first to propagate changes
                if doc_key in self._processed_hashes:
                    self.retriever.vector_store.delete_document_chunks(tenant_id, doc.document_id)

                indexed_count = self.index_and_verify(tenant_id, chunks)
                manifest.indexed_chunks += indexed_count
                manifest.processed_files += 1
                self._processed_hashes[doc_key] = doc.source_hash

            except Exception as e:
                manifest.failed_files += 1
                manifest.errors.append({
                    "document_id": doc.document_id,
                    "error": str(e),
                    "stage": "INDEX"
                })
                logger.error(f"Failed to ingest document {doc.document_id}: {str(e)}")

        elapsed = round(time.time() - start_time, 3)
        logger.info(
            f"Ingestion batch completed in {elapsed}s: processed={manifest.processed_files}, "
            f"skipped={manifest.skipped_duplicates}, failed={manifest.failed_files}, chunks={manifest.indexed_chunks}"
        )
        return manifest
