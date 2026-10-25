"""Unit tests for Workstream A: Legacy document extraction, chunking, and ETL."""

import hashlib
import io
import pytest
from pypdf import PdfWriter
from sentinel.core.models import ClearanceLevel
from sentinel.etl.chunker import StructureAwareChunker
from sentinel.etl.extractors import CSVExtractor, MarkdownExtractor, PDFExtractor
from sentinel.etl.pipeline import IngestionPipeline
from sentinel.etl.schemas import DocumentType, RawDocument
from sentinel.vector.chroma import ChromaVectorStore
from sentinel.vector.hybrid import HybridRetriever


def generate_sample_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def test_pdf_extractor():
    pdf_bytes = generate_sample_pdf_bytes()
    raw_doc = RawDocument(
        document_id="doc_pdf_1",
        filename="report.pdf",
        file_type=DocumentType.PDF,
        content_bytes=pdf_bytes,
        tenant_id="tenant-alpha",
        department="finance",
        source_hash=hashlib.sha256(pdf_bytes).hexdigest(),
    )
    extractor = PDFExtractor()
    result = extractor.extract(raw_doc)
    assert result.document_id == "doc_pdf_1"
    assert result.file_type == DocumentType.PDF
    assert result.parser_version == "1.0.0"


def test_csv_extractor():
    csv_text = "SKU,Product,Price,Quantity\nSKU-101,Microchip,12.50,1500\nSKU-102,Transceiver,85.00,400\n"
    csv_bytes = csv_text.encode("utf-8")
    raw_doc = RawDocument(
        document_id="doc_csv_1",
        filename="inventory.csv",
        file_type=DocumentType.CSV,
        content_bytes=csv_bytes,
        tenant_id="tenant-alpha",
        department="operations",
        source_hash=hashlib.sha256(csv_bytes).hexdigest(),
    )
    extractor = CSVExtractor()
    result = extractor.extract(raw_doc)
    assert len(result.items) == 2
    assert result.items[0].row_id == 1
    assert "SKU: SKU-101" in result.items[0].text
    assert "Product: Microchip" in result.items[0].text


def test_markdown_extractor():
    md_text = (
        "# Enterprise Architecture\n\n"
        "This is top level architecture.\n\n"
        "## Security Protocols\n\n"
        "Zero-trust tenant boundary enforcement.\n\n"
        "```python\n"
        "def auth(): pass\n"
        "```\n"
    )
    raw_doc = RawDocument(
        document_id="doc_md_1",
        filename="arch.md",
        file_type=DocumentType.MARKDOWN,
        content_bytes=md_text.encode("utf-8"),
        tenant_id="tenant-alpha",
        department="engineering",
        source_hash=hashlib.sha256(md_text.encode("utf-8")).hexdigest(),
    )
    extractor = MarkdownExtractor()
    result = extractor.extract(raw_doc)
    assert len(result.items) >= 2
    assert "Enterprise Architecture" in result.items[0].heading_hierarchy
    assert "Security Protocols" in result.items[1].heading_hierarchy


def test_structure_aware_chunker():
    md_text = "# Guidelines\n\nFirst paragraph with key rules. Second sentence.\n\nAnother paragraph.\n"
    raw_doc = RawDocument(
        document_id="doc_chunk_1",
        filename="guidelines.md",
        file_type=DocumentType.MARKDOWN,
        content_bytes=md_text.encode("utf-8"),
        tenant_id="tenant-alpha",
        department="engineering",
        source_hash="hash123",
    )
    extractor = MarkdownExtractor()
    extraction = extractor.extract(raw_doc)
    chunker = StructureAwareChunker()
    chunks = chunker.chunk(extraction, raw_doc, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 0
    for chk in chunks:
        assert chk.document_id == "doc_chunk_1"
        assert chk.tenant_id == "tenant-alpha"
        assert chk.content_hash != ""


def test_ingestion_pipeline_deduplication(tmp_path):
    store = ChromaVectorStore(persist_dir=tmp_path / "chroma")
    retriever = HybridRetriever(vector_store=store)
    pipeline = IngestionPipeline(retriever=retriever)

    csv_text = "id,name,value\n1,alpha,100\n2,beta,200\n"
    raw_doc = RawDocument(
        document_id="doc_dup_1",
        filename="data.csv",
        file_type=DocumentType.CSV,
        content_bytes=csv_text.encode("utf-8"),
        tenant_id="tenant-alpha",
        department="finance",
        source_hash=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
    )

    # First run
    m1 = pipeline.ingest_batch(job_id="job-1", tenant_id="tenant-alpha", documents=[raw_doc])
    assert m1.processed_files == 1
    assert m1.skipped_duplicates == 0

    # Second run with exact same file -> should be skipped as duplicate
    m2 = pipeline.ingest_batch(job_id="job-2", tenant_id="tenant-alpha", documents=[raw_doc])
    assert m2.processed_files == 0
    assert m2.skipped_duplicates == 1
