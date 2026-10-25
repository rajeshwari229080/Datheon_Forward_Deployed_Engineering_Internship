"""RAG pipeline query rewriting and authorized retrieval orchestrator."""

import re
import time
from typing import Dict, List, Optional, Tuple
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.core.models import UserIdentity
from sentinel.vector.chroma import ScoredChunk
from sentinel.vector.hybrid import HybridRetriever
from sentinel.vector.reranker import BaseReranker, get_reranker

logger = get_logger("sentinel.rag.pipeline")


class QueryRewriter:
    """Sanitizes and expands search queries while neutralizing injection patterns."""

    INJECTION_PATTERNS = [
        re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions"),
        re.compile(r"(?i)system\s*:\s*"),
        re.compile(r"(?i)disregard\s+system\s+prompt"),
        re.compile(r"(?i)you\s+are\s+now\s+an\s+unrestricted"),
        re.compile(r"(?i)output\s+all\s+(passwords|secrets|keys)"),
    ]

    def rewrite(self, query: str) -> str:
        clean = query.strip()
        # Neutralize direct injection triggers
        for pattern in self.INJECTION_PATTERNS:
            clean = pattern.sub(" ", clean)

        # Collapse whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean or query


class RAGPipeline:
    """Orchestrates authorized multi-stage retrieval:

    AUTHENTICATE -> RESOLVE POLICY -> REWRITE QUERY -> RETRIEVE CANDIDATES -> RERANK
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Optional[BaseReranker] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.retriever = retriever
        self.reranker = reranker or get_reranker(self.settings)
        self.rewriter = QueryRewriter()

    def retrieve_authorized_evidence(
        self,
        query: str,
        user: UserIdentity,
        top_k: Optional[int] = None,
    ) -> Tuple[str, List[ScoredChunk], Dict[str, float]]:
        """Executes authorized candidate retrieval and returns rewritten query, ranked chunks, and timings."""
        timings: Dict[str, float] = {}

        # Stage 1: Query Sanitization & Rewrite
        t0 = time.time()
        sanitized_query = self.rewriter.rewrite(query)
        timings["rewrite_ms"] = round((time.time() - t0) * 1000, 2)

        # Stage 2: Authorized Hybrid Retrieval (Chroma + BM25)
        t1 = time.time()
        candidate_k = (top_k or self.settings.retrieval_top_k) * 2
        raw_candidates = self.retriever.search(
            query=sanitized_query,
            user=user,
            top_k=candidate_k,
        )
        timings["retrieval_ms"] = round((time.time() - t1) * 1000, 2)

        # Stage 3: Cross-Encoder Reranking & Grounding Threshold Filtering
        t2 = time.time()
        final_top_k = top_k or self.settings.rerank_top_k
        reranked_chunks = self.reranker.rerank(
            query=sanitized_query,
            candidates=raw_candidates,
            top_k=final_top_k,
        )
        timings["rerank_ms"] = round((time.time() - t2) * 1000, 2)

        return sanitized_query, reranked_chunks, timings
