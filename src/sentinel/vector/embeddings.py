"""Embedding provider interfaces and deterministic local implementations."""

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger

logger = get_logger("sentinel.vector.embeddings")


class BaseEmbeddingProvider(ABC):
    """Abstract interface for dense embedding generation."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single query or document string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic, zero-dependency embedding provider based on text hashing.

    Produces reproducible, unit-normalized vectors suitable for cosine similarity in ChromaDB.
    """

    def __init__(self, dimension: int = 384, model_name: str = "sentinel-mock-embed-v1"):
        self._dimension = dimension
        self.model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> List[float]:
        # Generate deterministic floats based on MD5 and SHA256 rolling digest
        vec = []
        clean = text.strip().lower()
        if not clean:
            return [0.0] * self._dimension

        # Generate seed words
        words = clean.split()
        for i in range(self._dimension):
            h_input = f"{clean}:{i}:{len(words)}"
            digest = hashlib.sha256(h_input.encode("utf-8")).digest()
            val = (int.from_bytes(digest[:4], byteorder="big") / 2147483648.0) - 1.0

            # Boost semantic similarity for identical terms
            for word in words:
                word_hash = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                if (word_hash % self._dimension) == i:
                    val += 1.5

            vec.append(val)

        # L2 Unit Normalization for true Cosine Distance
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            return [v / norm for v in vec]
        return vec

    def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Adapter for local Ollama embedding models (e.g. nomic-embed-text)."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text", dimension: int = 768):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                res.raise_for_status()
                data = res.json()
                return data["embedding"]
        except Exception as e:
            logger.warning(f"Ollama embedding failed ({str(e)}), falling back to deterministic mock.")
            fallback = MockEmbeddingProvider(dimension=self._dimension)
            return fallback.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_provider(settings: Optional[Settings] = None) -> BaseEmbeddingProvider:
    """Factory creating the configured embedding provider."""
    cfg = settings or get_settings()
    if cfg.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(model=cfg.embedding_model_name, dimension=cfg.embedding_dimension)
    return MockEmbeddingProvider(dimension=cfg.embedding_dimension, model_name=cfg.embedding_model_name)
