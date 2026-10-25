"""Citation resolution, exact provenance mapping, and hallucination verification."""

from typing import List, Optional
from pydantic import BaseModel, Field
from sentinel.etl.schemas import DocumentChunk


class Citation(BaseModel):
    """Structured verifiable citation bound to retrieved evidence."""
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    row_id: Optional[int] = None
    heading_path: Optional[str] = None
    snippet: str
    source_hash: str
    verified: bool = True


class CitationResolver:
    """Extracts, validates, and cross-references citations against retrieved evidence."""

    @staticmethod
    def resolve_from_chunks(chunks: List[DocumentChunk]) -> List[Citation]:
        """Maps authorized evidence chunks into explicit, verifiable citations."""
        citations: List[Citation] = []
        for chunk in chunks:
            snippet = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    row_id=chunk.row_id,
                    heading_path=chunk.heading_path,
                    snippet=snippet,
                    source_hash=chunk.source_hash,
                    verified=True,
                )
            )
        return citations

    @staticmethod
    def verify_grounding(
        citations: List[Citation],
        evidence_chunks: List[DocumentChunk],
    ) -> bool:
        """Verifies that each citation corresponds directly to an authorized retrieved chunk."""
        valid_chunk_ids = {c.chunk_id for c in evidence_chunks}
        for cit in citations:
            if cit.chunk_id not in valid_chunk_ids:
                return False
        return True
