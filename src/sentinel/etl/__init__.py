"""Sentinel ETL package for legacy document ingestion and vector transformation."""

from sentinel.etl.schemas import (
    RawDocument,
    DocumentChunk,
    IngestionManifest,
    IngestionJob,
    DocumentType,
    ExtractionItem,
    ExtractionResult,
    IngestionStatus,
)
from sentinel.etl.base import BaseExtractor, BaseChunker
from sentinel.etl.chunker import StructureAwareChunker
from sentinel.etl.pipeline import IngestionPipeline

__all__ = [
    "RawDocument",
    "DocumentChunk",
    "IngestionManifest",
    "IngestionJob",
    "DocumentType",
    "ExtractionItem",
    "ExtractionResult",
    "IngestionStatus",
    "BaseExtractor",
    "BaseChunker",
    "StructureAwareChunker",
    "IngestionPipeline",
]
