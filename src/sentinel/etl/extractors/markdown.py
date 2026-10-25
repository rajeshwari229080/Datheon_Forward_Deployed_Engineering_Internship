"""Markdown structural extractor with heading hierarchy and code block preservation."""

import re
from typing import Dict, List
from sentinel.etl.base import BaseExtractor
from sentinel.etl.schemas import DocumentType, ExtractionItem, ExtractionResult, RawDocument


class MarkdownExtractor(BaseExtractor):
    """Parses Markdown documents preserving heading hierarchies and section paths."""

    def __init__(self, parser_version: str = "1.0.0"):
        self._version = parser_version

    @property
    def version(self) -> str:
        return self._version

    def extract(self, document: RawDocument) -> ExtractionResult:
        items: List[ExtractionItem] = []
        warnings: List[str] = []

        try:
            content = document.content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = document.content_bytes.decode("latin-1")
            except Exception as e:
                warnings.append(f"Failed to decode Markdown content: {str(e)}")
                return ExtractionResult(
                    document_id=document.document_id,
                    file_type=DocumentType.MARKDOWN,
                    items=[],
                    parser_version=self.version,
                    source_hash=document.source_hash,
                    warnings=warnings,
                )

        lines = content.splitlines()
        current_headings: Dict[int, str] = {}  # level -> heading text
        current_section_lines: List[str] = []
        in_code_block = False

        def get_current_heading_path() -> List[str]:
            sorted_levels = sorted(current_headings.keys())
            return [current_headings[lvl] for lvl in sorted_levels]

        def flush_section():
            if current_section_lines:
                text_block = "\n".join(current_section_lines).strip()
                if text_block:
                    hierarchy = get_current_heading_path()
                    items.append(
                        ExtractionItem(
                            text=text_block,
                            heading_hierarchy=hierarchy,
                            item_metadata={"heading_path": " > ".join(hierarchy)},
                        )
                    )
                current_section_lines.clear()

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("```"):
                in_code_block = not in_code_block
                current_section_lines.append(line)
                continue

            if not in_code_block:
                heading_match = heading_pattern.match(trimmed)
                if heading_match:
                    flush_section()
                    level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()

                    # Clear deeper heading levels
                    levels_to_remove = [lvl for lvl in current_headings if lvl >= level]
                    for lvl in levels_to_remove:
                        del current_headings[lvl]

                    current_headings[level] = heading_text
                    continue

            current_section_lines.append(line)

        flush_section()

        return ExtractionResult(
            document_id=document.document_id,
            file_type=DocumentType.MARKDOWN,
            items=items,
            parser_version=self.version,
            source_hash=document.source_hash,
            metadata={"sections_extracted": len(items)},
            warnings=warnings,
        )
