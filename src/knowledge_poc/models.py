from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SourcePage:
    page_id: str
    space_id: str
    parent_id: str | None
    title: str
    version: int
    storage_html: str
    source_url: str
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    page_id: str
    chunk_index: int
    content: str
    content_hash: str
    heading_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

