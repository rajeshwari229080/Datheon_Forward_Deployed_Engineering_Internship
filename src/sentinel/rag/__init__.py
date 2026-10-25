"""Sentinel RAG package for adversarially tested multi-tenant retrieval-augmented generation."""

from sentinel.rag.pipeline import RAGPipeline, QueryRewriter
from sentinel.rag.context import ContextManager
from sentinel.rag.citations import Citation, CitationResolver
from sentinel.rag.generator import (
    GroundedGenerator,
    RAGQueryResponse,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    BaseLLMAdapter,
    MockLLMAdapter,
)

__all__ = [
    "RAGPipeline",
    "QueryRewriter",
    "ContextManager",
    "Citation",
    "CitationResolver",
    "GroundedGenerator",
    "RAGQueryResponse",
    "INSUFFICIENT_EVIDENCE_MESSAGE",
    "BaseLLMAdapter",
    "MockLLMAdapter",
]
