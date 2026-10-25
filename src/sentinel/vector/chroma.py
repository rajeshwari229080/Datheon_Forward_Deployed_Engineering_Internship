"""ChromaDB vector store adapter with strict metadata filtering and provenance preservation."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentinel.core.config import Settings, get_settings
from sentinel.core.logging import get_logger
from sentinel.core.models import ClearanceLevel, UserIdentity
from sentinel.etl.schemas import DocumentChunk
from sentinel.vector.embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = get_logger("sentinel.vector.chroma")


class ScoredChunk:
    """Retrieved chunk bundled with similarity score and distance."""
    def __init__(self, chunk: DocumentChunk, score: float, distance: float):
        self.chunk = chunk
        self.score = score
        self.distance = distance


class ChromaVectorStore:
    """Manages persistent ChromaDB vector storage with strict tenant authorization boundaries."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        collection_prefix: str = "sentinel",
    ):
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_provider = embedding_provider or get_embedding_provider(settings)
        self.collection_prefix = collection_prefix

        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
        )

    def _get_collection(self, tenant_id: str):
        """Retrieve or create tenant-isolated ChromaDB collection with cosine distance."""
        safe_tenant = "".join(c if c.isalnum() or c in "-_" else "_" for c in tenant_id)
        coll_name = f"{self.collection_prefix}_{safe_tenant}"
        return self.client.get_or_create_collection(
            name=coll_name,
            metadata={"hnsw:space": "cosine", "tenant_id": tenant_id},
        )

    def index_chunks(self, tenant_id: str, chunks: List[DocumentChunk]) -> int:
        """Batch index document chunks with dense embeddings and metadata."""
        if not chunks:
            return 0

        coll = self._get_collection(tenant_id)
        texts = [c.text for c in chunks]
        embeddings = self.embedding_provider.embed_batch(texts)
        ids = [c.chunk_id for c in chunks]
        metadatas = [c.to_metadata_dict() for c in chunks]

        # Chroma upsert ensures idempotency
        coll.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(chunks)} chunks for tenant {tenant_id} into collection {coll.name}")
        return len(chunks)

    def search(
        self,
        query: str,
        user: UserIdentity,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredChunk]:
        """Search chunks with mandatory zero-trust authorization metadata filters."""
        coll = self._get_collection(user.tenant_id)

        # Enforce strict metadata filtering outside LLM
        # 1. Tenant boundary is isolated by collection
        # 2. Clearance filter: user clearance rank must be >= chunk clearance rank
        allowed_clearances = [
            lvl.value for lvl in ClearanceLevel if user.clearance.satisfies(lvl)
        ]

        where_clauses: List[Dict[str, Any]] = [
            {"clearance": {"$in": allowed_clearances}}
        ]

        # 3. Department boundary filter (if not admin)
        if user.role.value != "admin" and user.department.lower() != "all":
            allowed_depts = [user.department.lower()] + [d.lower() for d in user.allowed_departments]
            where_clauses.append({"department": {"$in": allowed_depts}})

        # Merge user filters if provided
        if filter_metadata:
            for k, v in filter_metadata.items():
                where_clauses.append({k: v})

        final_where: Dict[str, Any]
        if len(where_clauses) == 1:
            final_where = where_clauses[0]
        else:
            final_where = {"$and": where_clauses}

        query_embedding = self.embedding_provider.embed_text(query)

        try:
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=final_where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning(f"Vector search query error (empty collection or no matches): {str(e)}")
            return []

        scored_chunks: List[ScoredChunk] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for i in range(len(ids)):
            meta = metas[i]
            dist = distances[i]
            # In cosine space, similarity = 1 - distance
            score = max(0.0, min(1.0, 1.0 - dist))

            chunk = DocumentChunk(
                chunk_id=meta.get("chunk_id", ids[i]),
                document_id=meta.get("document_id", "unknown"),
                filename=meta.get("filename", "unknown"),
                tenant_id=meta.get("tenant_id", user.tenant_id),
                department=meta.get("department", "general"),
                clearance=ClearanceLevel(meta.get("clearance", "internal")),
                text=docs[i],
                chunk_index=int(meta.get("chunk_index", 0)),
                page_number=int(meta.get("page_number", -1)) if int(meta.get("page_number", -1)) >= 0 else None,
                row_id=int(meta.get("row_id", -1)) if int(meta.get("row_id", -1)) >= 0 else None,
                heading_path=meta.get("heading_path") or None,
                content_hash=meta.get("content_hash", ""),
                source_hash=meta.get("source_hash", ""),
                parser_version=meta.get("parser_version", "1.0.0"),
            )
            scored_chunks.append(ScoredChunk(chunk=chunk, score=score, distance=dist))

        return scored_chunks

    def delete_document_chunks(self, tenant_id: str, document_id: str) -> int:
        """Deletes all chunks associated with a specific document."""
        coll = self._get_collection(tenant_id)
        try:
            coll.delete(where={"document_id": document_id})
            logger.info(f"Deleted chunks for document {document_id} from tenant {tenant_id}")
            return 1
        except Exception as e:
            logger.warning(f"Failed to delete chunks for document {document_id}: {str(e)}")
            return 0
