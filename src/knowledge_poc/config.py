from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    confluence_base_url: str | None
    confluence_email: str | None
    confluence_api_token: str | None
    confluence_space_id: str | None
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    chunk_size: int
    chunk_overlap: int
    poll_interval_seconds: int

    @classmethod
    def from_env(cls, require_confluence: bool = False) -> "Settings":
        base_url = os.getenv("CONFLUENCE_BASE_URL")
        email = os.getenv("CONFLUENCE_EMAIL")
        token = os.getenv("CONFLUENCE_API_TOKEN")
        space_id = os.getenv("CONFLUENCE_SPACE_ID")
        if require_confluence:
            base_url = _required("CONFLUENCE_BASE_URL")
            email = _required("CONFLUENCE_EMAIL")
            token = _required("CONFLUENCE_API_TOKEN")
            space_id = _required("CONFLUENCE_SPACE_ID")
        return cls(
            database_url=os.getenv(
                "DATABASE_URL", "postgresql://knowledge:knowledge@localhost:5432/knowledge_poc"
            ),
            confluence_base_url=base_url.rstrip("/") if base_url else None,
            confluence_email=email,
            confluence_api_token=token,
            confluence_space_id=space_id,
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local").lower(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "384")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
        )
