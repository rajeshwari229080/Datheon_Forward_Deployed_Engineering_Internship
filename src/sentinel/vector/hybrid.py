"""Hybrid retrieval combining dense vector similarity and sparse BM25 with Reciprocal Rank Fusion."""

from typing import Dict, List, Optional
from sentinel.core.logging import get_logger
from sentinel.core.models import UserIdentity
from sentinel.core.security import PolicyEngine
from sentinel.etl.schemas import DocumentChunk
from sentinel.vector.bm25 import BM25Index
from sentinel.vector.chroma import ChromaVectorStore, ScoredChunk

logger = get_logger("sentinel.vector.hybrid")


class HybridRetriever:
    """Combines dense semantic vector retrieval with sparse lexical BM25 matching."""

    def __init__(self, vector_store: ChromaVectorStore, rrf_k: int = 60):
        self.vector_store = vector_store
        self.rrf_k = rrf_k
        self._bm25_indices: Dict[str, BM25Index] = {}

    def get_bm25_index(self, tenant_id: str) -> BM25Index:
        """Get or initialize tenant-partitioned BM25 index."""
        if tenant_id not in self._bm25_indices:
            self._bm25_indices[tenant_id] = BM25Index()
        return self._bm25_indices[tenant_id]

    def index_chunks(self, tenant_id: str, chunks: List[DocumentChunk]) -> None:
        """Synchronously index chunks in both ChromaDB and BM25."""
        self.vector_store.index_chunks(tenant_id, chunks)
        bm25 = self.get_bm25_index(tenant_id)
        bm25.add_chunks(chunks)

    def search(
        self,
        query: str,
        user: UserIdentity,
        top_k: int = 5,
        vector_weight: float = 0.7,
        lexical_weight: float = 0.3,
    ) -> List[ScoredChunk]:
        """Perform hybrid search with Reciprocal Rank Fusion and zero-trust policy enforcement."""
        # 1. Dense vector candidates
        dense_results = self.vector_store.search(query=query, user=user, top_k=top_k * 2)

        # 2. Sparse BM25 candidates
        bm25 = self.get_bm25_index(user.tenant_id)
        sparse_results = bm25.search(query=query, top_k=top_k * 2)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        for rank, item in enumerate(dense_results, start=1):
            cid = item.chunk.chunk_id
            chunk_map[cid] = item.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + vector_weight * (1.0 / (self.rrf_k + rank))

        for rank, (chunk, _raw_bm25) in enumerate(sparse_results, start=1):
            # Authorize BM25 candidate before adding
            if not PolicyEngine.can_access_document(
                user=user,
                document_tenant_id=chunk.tenant_id,
                document_department=chunk.department,
                document_clearance=chunk.clearance,
            ):
                continue

            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + lexical_weight * (1.0 / (self.rrf_k + rank))

        if not rrf_scores:
            return []

        # Sort by composite RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        max_score = max(rrf_scores.values()) if rrf_scores else 1.0
        final_results: List[ScoredChunk] = []

        for cid in sorted_cids:
            normalized_score = rrf_scores[cid] / max_score
            final_results.append(
                ScoredChunk(
                    chunk=chunk_map[cid],
                    score=round(normalized_score, 4),
                    distance=round(1.0 - normalized_score, 4),
                )
            )

        logger.info(f"Hybrid retrieval returned {len(final_results)} authorized candidates for user {user.user_id}")
        return final_results
