"""Abstract base classes and interfaces for document extraction and chunking."""

from abc import ABC, abstractmethod
from typing import List
from sentinel.etl.schemas import ExtractionResult, RawDocument, DocumentChunk


class BaseExtractor(ABC):
    """Abstract interface for format-specific text and provenance extractors."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Parser version string for provenance auditing."""
        pass

    @abstractmethod
    def extract(self, document: RawDocument) -> ExtractionResult:
        """Parse raw document bytes into structured items with provenance metadata."""
        pass


class BaseChunker(ABC):
    """Abstract interface for structure-aware and semantic chunking."""

    @abstractmethod
    def chunk(
        self,
        extraction: ExtractionResult,
        raw_doc: RawDocument,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> List[DocumentChunk]:
        """Convert extracted items into verifiable chunks with cryptographic fingerprints."""
        pass
