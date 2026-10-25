"""Sentinel ETL package for legacy document ingestion and vector transformation."""

from sentinel.etl.schemas import RawDocument, DocumentChunk, IngestionManifest, IngestionJob
from sentinel.etl.base import BaseExtractor, BaseChunker

__all__ = [
    "RawDocument",
    "DocumentChunk",
    "IngestionManifest",
    "IngestionJob",
    "BaseExtractor",
    "BaseChunker",
]
