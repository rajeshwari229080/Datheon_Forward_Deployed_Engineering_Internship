"""PDF document extractor preserving exact page-level provenance."""

import io
import re
from typing import List
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from sentinel.etl.base import BaseExtractor
from sentinel.etl.schemas import DocumentType, ExtractionItem, ExtractionResult, RawDocument


class PDFExtractor(BaseExtractor):
    """Extracts text from PDF documents preserving page number provenance."""

    def __init__(self, parser_version: str = "1.0.0"):
        self._version = parser_version

    @property
    def version(self) -> str:
        return self._version

    def extract(self, document: RawDocument) -> ExtractionResult:
        items: List[ExtractionItem] = []
        warnings: List[str] = []

        try:
            stream = io.BytesIO(document.content_bytes)
            reader = PdfReader(stream)

            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    warnings.append(f"Document {document.document_id} is encrypted; extraction may be incomplete.")

            total_pages = len(reader.pages)
            if total_pages == 0:
                warnings.append("PDF contains 0 pages.")

            for page_idx, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                # Normalize whitespace while preserving line structure
                normalized_text = re.sub(r"[ \t]+", " ", raw_text).strip()

                if not normalized_text:
                    warnings.append(f"Page {page_idx} is empty or contains non-extractable text.")
                    continue

                items.append(
                    ExtractionItem(
                        text=normalized_text,
                        page_number=page_idx,
                        item_metadata={
                            "total_pages": total_pages,
                            "page_index": page_idx,
                        },
                    )
                )

        except PyPdfError as pe:
            warnings.append(f"PyPdfError during extraction: {str(pe)}")
        except Exception as e:
            warnings.append(f"Unexpected error during PDF parsing: {str(e)}")

        return ExtractionResult(
            document_id=document.document_id,
            file_type=DocumentType.PDF,
            items=items,
            parser_version=self.version,
            source_hash=document.source_hash,
            metadata={"extracted_pages": len(items)},
            warnings=warnings,
        )
