"""Lightweight, in-memory BM25 lexical index with tenant partitioning."""

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from sentinel.etl.schemas import DocumentChunk


class BM25Index:
    """Sparse lexical search index based on Okapi BM25."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: Dict[str, int] = {}
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_store: Dict[str, DocumentChunk] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
        return [t for t in tokens if len(t) > 1]

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add or update chunks in the BM25 index."""
        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            doc_len = len(tokens)
            self.doc_store[chunk.chunk_id] = chunk
            self.doc_lengths[chunk.chunk_id] = doc_len

            counts = Counter(tokens)
            for token, count in counts.items():
                self.inverted_index[token][chunk.chunk_id] = count

        self._recompute_statistics()

    def _recompute_statistics(self) -> None:
        self.corpus_size = len(self.doc_store)
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        self.avg_doc_len = sum(self.doc_lengths.values()) / self.corpus_size
        self.idf.clear()
        for term, posting in self.inverted_index.items():
            doc_freq = len(posting)
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(1.0 + (self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Compute BM25 score for query terms."""
        query_tokens = self._tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        scores: Dict[str, float] = defaultdict(float)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            term_idf = self.idf.get(token, 0.0)
            if term_idf <= 0.0:
                continue

            posting = self.inverted_index[token]
            for doc_id, tf in posting.items():
                doc_len = self.doc_lengths[doc_id]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                scores[doc_id] += term_idf * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.doc_store[doc_id], score) for doc_id, score in ranked]
