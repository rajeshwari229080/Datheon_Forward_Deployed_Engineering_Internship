"""Central configuration management for Sentinel using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment & Server
    env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    app_name: str = "Sentinel Enterprise AI Fabric"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000

    # Data & Persistence
    data_dir: Path = Field(default=Path("./data"))
    chroma_persist_dir: Path = Field(default=Path("./data/chroma"))
    chroma_collection_prefix: str = "sentinel"

    # Ingestion & ETL Limits
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    default_chunk_size: int = 512
    default_chunk_overlap: int = 64
    max_batch_concurrency: int = 4

    # Vector & Embeddings
    embedding_provider: Literal["mock", "local", "ollama"] = "mock"
    embedding_model_name: str = "sentinel-embed-v1"
    embedding_dimension: int = 384

    # Reranking & Retrieval
    reranker_provider: Literal["mock", "cross_encoder"] = "mock"
    retrieval_top_k: int = 5
    rerank_top_k: int = 3
    grounding_score_threshold: float = 0.45

    # LLM & Generation
    llm_provider: Literal["mock", "ollama"] = "mock"
    llm_model_name: str = "llama3:8b"
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 30.0

    # Security & Agent Governance
    agent_approval_secret: str = "sentinel-governance-secret-key-prod-ready"
    agent_approval_ttl_seconds: int = 900  # 15 minutes
    rate_limit_per_minute: int = 120
    audit_log_path: Path = Field(default=Path("./data/audit/audit_events.jsonl"))

    # Logging & Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json_format: bool = True
    prometheus_multiproc_dir: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
