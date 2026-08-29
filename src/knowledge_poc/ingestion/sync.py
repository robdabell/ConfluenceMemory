from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from knowledge_poc.confluence.client import ConfluenceClient
from knowledge_poc.embeddings.client import Embeddings
from knowledge_poc.storage.database import Database
from knowledge_poc.transformation.chunker import chunk_page
from knowledge_poc.transformation.cleaner import clean_storage_html
from knowledge_poc.transformation.hashing import sha256_text, structure_hash

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    discovered: int = 0
    embedded_pages: int = 0
    embedded_chunks: int = 0
    skipped: int = 0
    tombstoned: int = 0


class Synchroniser:
    def __init__(
        self,
        confluence: ConfluenceClient,
        database: Database,
        embeddings: Embeddings,
        chunk_size: int,
        chunk_overlap: int,
    ):
        self.confluence = confluence
        self.database = database
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def run(self, space_id: str, full: bool = False) -> SyncResult:
        scope = f"confluence-space:{space_id}"
        watermark = None if full else self.database.get_watermark(scope)
        # Small overlap protects timestamp-boundary updates; hashes make repeats cheap.
        since = watermark - timedelta(minutes=5) if watermark else None
        result = SyncResult()
        seen: set[str] = set()
        newest = watermark

        for page in self.confluence.iter_pages(space_id, since=since):
            result.discovered += 1
            seen.add(page.page_id)
            newest = max(filter(None, [newest, page.updated_at]), default=page.updated_at)
            text = clean_storage_html(page.storage_html, page.title)
            content_digest = sha256_text(text)
            structure_digest = structure_hash(page.title, page.parent_id, text)
            previous = self.database.get_page_state(page.page_id)
            if (
                previous
                and previous["content_hash"] == content_digest
                and previous["structure_hash"] == structure_digest
                and previous["deleted_at"] is None
            ):
                self.database.touch_page(page.page_id)
                result.skipped += 1
                continue
            chunks = chunk_page(page.page_id, text, self.chunk_size, self.chunk_overlap)
            vectors = self.embeddings.embed_documents([chunk.content for chunk in chunks])
            self.database.replace_page(
                page, content_digest, structure_digest, chunks, vectors
            )
            result.embedded_pages += 1
            result.embedded_chunks += len(chunks)
            logger.info("Indexed page %s version %s (%s chunks)", page.page_id, page.version, len(chunks))

        if full:
            result.tombstoned = self.database.tombstone_missing(space_id, seen)
        if newest:
            self.database.set_watermark(scope, newest)
        return result

