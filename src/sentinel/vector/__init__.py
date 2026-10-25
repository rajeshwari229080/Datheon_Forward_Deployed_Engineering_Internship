"""Vector operations, embedding providers, ChromaDB integration, and hybrid search."""

from sentinel.vector.embeddings import BaseEmbeddingProvider, MockEmbeddingProvider, get_embedding_provider
from sentinel.vector.chroma import ChromaVectorStore, ScoredChunk
from sentinel.vector.bm25 import BM25Index
from sentinel.vector.hybrid import HybridRetriever

__all__ = [
    "BaseEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
    "ChromaVectorStore",
    "ScoredChunk",
    "BM25Index",
    "HybridRetriever",
]
