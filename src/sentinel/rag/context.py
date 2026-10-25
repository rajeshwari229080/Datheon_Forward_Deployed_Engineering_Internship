"""Context deduplication and token-budget management for secure RAG prompts."""

from typing import List, Set, Tuple
from sentinel.etl.schemas import DocumentChunk
from sentinel.vector.chroma import ScoredChunk


class ContextManager:
    """Manages context assembly, deduplication, and token budgeting."""

    def __init__(self, max_token_budget: int = 2048):
        self.max_token_budget = max_token_budget

    def _estimate_tokens(self, text: str) -> int:
        """Rough 4-chars-per-token heuristic."""
        return max(1, len(text) // 4)

    def assemble_deduplicated_context(
        self,
        scored_chunks: List[ScoredChunk],
    ) -> Tuple[str, List[DocumentChunk], int]:
        """Deduplicate chunks by content hash and fit strictly within token budget."""
        seen_hashes: Set[str] = set()
        selected_chunks: List[DocumentChunk] = []
        context_blocks: List[str] = []
        total_tokens = 0

        for item in scored_chunks:
            chunk = item.chunk
            if chunk.content_hash in seen_hashes:
                continue

            chunk_tokens = self._estimate_tokens(chunk.text)
            if total_tokens + chunk_tokens > self.max_token_budget:
                break

            seen_hashes.add(chunk.content_hash)
            selected_chunks.append(chunk)
            total_tokens += chunk_tokens

            provenance_tag = f"Document: {chunk.filename}"
            if chunk.page_number is not None:
                provenance_tag += f" | Page: {chunk.page_number}"
            if chunk.row_id is not None:
                provenance_tag += f" | Row: {chunk.row_id}"
            if chunk.heading_path:
                provenance_tag += f" | Section: {chunk.heading_path}"

            # Wrap in structured boundaries to prevent prompt injection leaks
            block = (
                f"<source_evidence id=\"{chunk.chunk_id}\" {provenance_tag}>\n"
                f"{chunk.text}\n"
                f"</source_evidence>"
            )
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)
        return formatted_context, selected_chunks, total_tokens
