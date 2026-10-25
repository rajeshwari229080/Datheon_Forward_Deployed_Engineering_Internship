"""Hybrid search and authorized RAG query endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sentinel.core.logging import get_logger
from sentinel.core.models import UserIdentity
from sentinel.core.security import resolve_user_identity
from sentinel.rag.generator import GroundedGenerator, RAGQueryResponse
from sentinel.rag.pipeline import RAGPipeline
from sentinel.telemetry.metrics import MODEL_LATENCY, RETRIEVAL_LATENCY
from sentinel.vector.chroma import ChromaVectorStore
from sentinel.vector.hybrid import HybridRetriever
from sentinel.vector.reranker import get_reranker

logger = get_logger("sentinel.api.routes.rag")

router = APIRouter(prefix="/api/v1", tags=["Search & RAG"])

# Shared pipeline instances
_vector_store = ChromaVectorStore()
_retriever = HybridRetriever(vector_store=_vector_store)
_reranker = get_reranker()
_rag_pipeline = RAGPipeline(retriever=_retriever, reranker=_reranker)
_generator = GroundedGenerator(rag_pipeline=_rag_pipeline)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search terms")
    top_k: int = Field(5, ge=1, le=50, description="Max candidates to retrieve")


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    row_id: Optional[int] = None
    heading_path: Optional[str] = None
    text: str
    score: float
    clearance: str


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]
    total_found: int
    tenant_id: str


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language enterprise question")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Max context chunks to retrieve")


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_documents(
    payload: SearchRequest,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Authorized hybrid search (dense + BM25) with zero-trust tenant and clearance filtering."""
    results = _retriever.search(query=payload.query, user=user, top_k=payload.top_k)

    hits: List[SearchHit] = []
    for item in results:
        chunk = item.chunk
        hits.append(
            SearchHit(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                filename=chunk.filename,
                page_number=chunk.page_number,
                row_id=chunk.row_id,
                heading_path=chunk.heading_path,
                text=chunk.text,
                score=item.score,
                clearance=chunk.clearance.value,
            )
        )

    return SearchResponse(
        query=payload.query,
        hits=hits,
        total_found=len(hits),
        tenant_id=user.tenant_id,
    )


@router.post("/rag/query", response_model=RAGQueryResponse, status_code=status.HTTP_200_OK)
def rag_query(
    payload: RAGQueryRequest,
    user: UserIdentity = Depends(resolve_user_identity),
):
    """Executes authorized RAG: rewrite, retrieve, rerank, grounding validation, and cited response."""
    response = _generator.query(query=payload.query, user=user, top_k=payload.top_k)

    # Record Prometheus latencies
    if "retrieval_ms" in response.timings_ms:
        RETRIEVAL_LATENCY.observe(response.timings_ms["retrieval_ms"] / 1000.0)
    if "generation_ms" in response.timings_ms:
        MODEL_LATENCY.observe(response.timings_ms["generation_ms"] / 1000.0)

    return response
