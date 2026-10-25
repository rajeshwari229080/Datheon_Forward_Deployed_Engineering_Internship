"""Structure-aware chunking engine with deterministic cryptographic hashing."""

import hashlib
import re
from typing import List
from sentinel.etl.base import BaseChunker
from sentinel.etl.schemas import DocumentChunk, ExtractionItem, ExtractionResult, RawDocument


class StructureAwareChunker(BaseChunker):
    """Splits extracted items into chunks while preserving provenance metadata and boundaries."""

    def __init__(self, parser_version: str = "1.0.0"):
        self.parser_version = parser_version

    def chunk(
        self,
        extraction: ExtractionResult,
        raw_doc: RawDocument,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for item in extraction.items:
            item_chunks = self._chunk_item_text(
                item=item,
                raw_doc=raw_doc,
                start_index=global_chunk_idx,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            chunks.extend(item_chunks)
            global_chunk_idx += len(item_chunks)

        return chunks

    def _chunk_item_text(
        self,
        item: ExtractionItem,
        raw_doc: RawDocument,
        start_index: int,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[DocumentChunk]:
        text = item.text.strip()
        if not text:
            return []

        # If text is smaller than chunk_size, keep as single atomic chunk
        if len(text) <= chunk_size:
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunk_id = f"{raw_doc.document_id}_chk_{start_index}_{content_hash[:8]}"
            heading_path = " > ".join(item.heading_hierarchy) if item.heading_hierarchy else None

            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=raw_doc.document_id,
                    filename=raw_doc.filename,
                    tenant_id=raw_doc.tenant_id,
                    department=raw_doc.department,
                    clearance=raw_doc.clearance,
                    text=text,
                    chunk_index=start_index,
                    page_number=item.page_number,
                    row_id=item.row_id,
                    heading_path=heading_path,
                    content_hash=content_hash,
                    source_hash=raw_doc.source_hash,
                    parser_version=self.parser_version,
                )
            ]

        # Splitting using paragraph and sentence boundaries
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        result_chunks: List[DocumentChunk] = []
        current_segment: List[str] = []
        current_len = 0
        idx = start_index

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            if current_len + len(sentence_clean) > chunk_size and current_segment:
                chunk_body = " ".join(current_segment)
                content_hash = hashlib.sha256(chunk_body.encode("utf-8")).hexdigest()
                chunk_id = f"{raw_doc.document_id}_chk_{idx}_{content_hash[:8]}"
                heading_path = " > ".join(item.heading_hierarchy) if item.heading_hierarchy else None

                result_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=raw_doc.document_id,
                        filename=raw_doc.filename,
                        tenant_id=raw_doc.tenant_id,
                        department=raw_doc.department,
                        clearance=raw_doc.clearance,
                        text=chunk_body,
                        chunk_index=idx,
                        page_number=item.page_number,
                        row_id=item.row_id,
                        heading_path=heading_path,
                        content_hash=content_hash,
                        source_hash=raw_doc.source_hash,
                        parser_version=self.parser_version,
                    )
                )
                idx += 1

                # Overlap logic: keep trailing sentence if within overlap budget
                overlap_budget = chunk_overlap
                kept_overlap: List[str] = []
                overlap_len = 0
                for prev in reversed(current_segment):
                    if overlap_len + len(prev) <= overlap_budget:
                        kept_overlap.insert(0, prev)
                        overlap_len += len(prev)
                    else:
                        break

                current_segment = kept_overlap
                current_len = sum(len(s) for s in current_segment)

            current_segment.append(sentence_clean)
            current_len += len(sentence_clean)

        if current_segment:
            chunk_body = " ".join(current_segment)
            content_hash = hashlib.sha256(chunk_body.encode("utf-8")).hexdigest()
            chunk_id = f"{raw_doc.document_id}_chk_{idx}_{content_hash[:8]}"
            heading_path = " > ".join(item.heading_hierarchy) if item.heading_hierarchy else None

            result_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=raw_doc.document_id,
                    filename=raw_doc.filename,
                    tenant_id=raw_doc.tenant_id,
                    department=raw_doc.department,
                    clearance=raw_doc.clearance,
                    text=chunk_body,
                    chunk_index=idx,
                    page_number=item.page_number,
                    row_id=item.row_id,
                    heading_path=heading_path,
                    content_hash=content_hash,
                    source_hash=raw_doc.source_hash,
                    parser_version=self.parser_version,
                )
            )

        return result_chunks
