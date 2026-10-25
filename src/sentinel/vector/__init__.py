"""Vector operations, embedding providers, ChromaDB integration, hybrid search, and reranking."""

from sentinel.vector.embeddings import BaseEmbeddingProvider, MockEmbeddingProvider, get_embedding_provider
from sentinel.vector.chroma import ChromaVectorStore, ScoredChunk
from sentinel.vector.bm25 import BM25Index
from sentinel.vector.hybrid import HybridRetriever
from sentinel.vector.reranker import BaseReranker, MockReranker, get_reranker

__all__ = [
    "BaseEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
    "ChromaVectorStore",
    "ScoredChunk",
    "BM25Index",
    "HybridRetriever",
    "BaseReranker",
    "MockReranker",
    "get_reranker",
]
