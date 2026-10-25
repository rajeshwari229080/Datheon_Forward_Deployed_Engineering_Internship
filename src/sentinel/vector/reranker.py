"""Cross-encoder reranking engine with threshold filtering."""

import re
from abc import ABC, abstractmethod
from typing import List, Optional
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.vector.chroma import ScoredChunk

logger = get_logger("sentinel.vector.reranker")


class BaseReranker(ABC):
    """Abstract interface for query-document cross-encoder reranking."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[ScoredChunk], top_k: int = 3) -> List[ScoredChunk]:
        """Score (query, document) pairs jointly and return reordered candidates."""
        pass


class MockReranker(BaseReranker):
    """Deterministic reranker prioritizing exact term overlap, query term density, and position."""

    def __init__(self, score_threshold: float = 0.35):
        self.score_threshold = score_threshold

    def rerank(self, query: str, candidates: List[ScoredChunk], top_k: int = 3) -> List[ScoredChunk]:
        if not candidates:
            return []

        query_tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9_-]+\b", query)]
        if not query_tokens:
            return candidates[:top_k]

        scored: List[ScoredChunk] = []
        for cand in candidates:
            doc_lower = cand.chunk.text.lower()
            doc_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", doc_lower)

            # Compute token matching coverage
            matches = sum(1 for q in query_tokens if q in doc_lower)
            coverage = matches / len(query_tokens)

            # Compute term frequency density in document
            term_freq = sum(doc_tokens.count(q) for q in query_tokens)
            density = min(1.0, term_freq / max(len(doc_tokens), 1) * 5.0)

            # Joint cross-encoder synthetic score combining prior score, coverage, and density
            joint_score = round(0.4 * cand.score + 0.4 * coverage + 0.2 * density, 4)

            if joint_score >= self.score_threshold:
                scored.append(ScoredChunk(chunk=cand.chunk, score=joint_score, distance=round(1.0 - joint_score, 4)))

        # Sort descending by rerank score
        reranked = sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
        logger.info(f"Reranker selected {len(reranked)} from {len(candidates)} candidates")
        return reranked


def get_reranker(settings: Optional[Settings] = None) -> BaseReranker:
    """Factory retrieving configured reranker instance."""
    cfg = settings or get_settings()
    return MockReranker(score_threshold=cfg.grounding_score_threshold)
