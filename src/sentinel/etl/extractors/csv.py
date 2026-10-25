"""CSV tabular document extractor preserving exact row-level provenance."""

import csv
import io
from typing import List
from sentinel.etl.base import BaseExtractor
from sentinel.etl.schemas import DocumentType, ExtractionItem, ExtractionResult, RawDocument


class CSVExtractor(BaseExtractor):
    """Normalizes tabular CSV records into natural language representations while tracking row IDs."""

    def __init__(self, parser_version: str = "1.0.0", max_rows: int = 10000):
        self._version = parser_version
        self.max_rows = max_rows

    @property
    def version(self) -> str:
        return self._version

    def extract(self, document: RawDocument) -> ExtractionResult:
        items: List[ExtractionItem] = []
        warnings: List[str] = []

        # Try multiple encodings
        text_content = ""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text_content = document.content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text_content:
            warnings.append(f"Failed to decode CSV document {document.document_id} with supported encodings.")
            return ExtractionResult(
                document_id=document.document_id,
                file_type=DocumentType.CSV,
                items=[],
                parser_version=self.version,
                source_hash=document.source_hash,
                metadata={},
                warnings=warnings,
            )

        try:
            reader = csv.reader(io.StringIO(text_content))
            headers: List[str] = []
            try:
                headers = [h.strip() for h in next(reader, [])]
            except Exception as e:
                warnings.append(f"Could not read CSV header: {str(e)}")

            if not headers:
                warnings.append("CSV document appears to have no headers or content.")

            for row_idx, row in enumerate(reader, start=1):
                if row_idx > self.max_rows:
                    warnings.append(f"Truncated CSV extraction at {self.max_rows} rows.")
                    break

                # Combine headers with values into a semantically rich structured sentence
                cell_pairs = []
                for idx, cell in enumerate(row):
                    col_name = headers[idx] if idx < len(headers) else f"Column_{idx+1}"
                    clean_cell = cell.strip()
                    if clean_cell:
                        cell_pairs.append(f"{col_name}: {clean_cell}")

                if not cell_pairs:
                    continue

                row_text = "; ".join(cell_pairs)
                items.append(
                    ExtractionItem(
                        text=row_text,
                        row_id=row_idx,
                        item_metadata={
                            "row_index": row_idx,
                            "column_count": len(row),
                            "headers": headers,
                        },
                    )
                )

        except Exception as e:
            warnings.append(f"CSV parsing error: {str(e)}")

        return ExtractionResult(
            document_id=document.document_id,
            file_type=DocumentType.CSV,
            items=items,
            parser_version=self.version,
            source_hash=document.source_hash,
            metadata={"row_count": len(items)},
            warnings=warnings,
        )
