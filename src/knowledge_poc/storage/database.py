from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from knowledge_poc.models import SourcePage, TextChunk


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            register_vector(connection)
            yield connection

    def migrate(self, migrations_dir: Path) -> list[str]:
        applied: list[str] = []
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migration (
                    version text PRIMARY KEY,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            rows = connection.execute("SELECT version FROM schema_migration").fetchall()
            applied_versions = {row[0] for row in rows}
            for path in sorted(migrations_dir.glob("*.sql")):
                if path.name in applied_versions:
                    continue
                connection.execute(path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migration(version) VALUES (%s) ON CONFLICT DO NOTHING",
                    (path.name,),
                )
                applied.append(path.name)
        return applied

    def get_page_state(self, page_id: str) -> dict | None:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT version, content_hash, structure_hash, deleted_at, metadata
                FROM source_page WHERE page_id=%s
                """,
                (page_id,),
            ).fetchone()

    def replace_page(
        self,
        page: SourcePage,
        content_hash: str,
        structure_hash: str,
        chunks: list[TextChunk],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and vector counts differ")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO source_page
                  (page_id, space_id, parent_id, title, version, content_hash, structure_hash,
                   source_url, updated_at, last_seen_at, deleted_at, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),NULL,%s)
                ON CONFLICT (page_id) DO UPDATE SET
                  space_id=EXCLUDED.space_id, parent_id=EXCLUDED.parent_id, title=EXCLUDED.title,
                  version=EXCLUDED.version, content_hash=EXCLUDED.content_hash,
                  structure_hash=EXCLUDED.structure_hash, source_url=EXCLUDED.source_url,
                  updated_at=EXCLUDED.updated_at, last_seen_at=now(), deleted_at=NULL,
                  metadata=EXCLUDED.metadata
                """,
                (
                    page.page_id,
                    page.space_id,
                    page.parent_id,
                    page.title,
                    page.version,
                    content_hash,
                    structure_hash,
                    page.source_url,
                    page.updated_at,
                    json.dumps(page.metadata),
                ),
            )
            connection.execute("DELETE FROM knowledge_chunk WHERE page_id=%s", (page.page_id,))
            for chunk, vector in zip(chunks, vectors, strict=True):
                metadata = {
                    **page.metadata,
                    **chunk.metadata,
                    "title": page.title,
                    "source_url": page.source_url,
                }
                connection.execute(
                    """
                    INSERT INTO knowledge_chunk
                      (chunk_id,page_id,chunk_index,heading_path,content,content_hash,embedding,metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        chunk.chunk_id,
                        chunk.page_id,
                        chunk.chunk_index,
                        chunk.heading_path,
                        chunk.content,
                        chunk.content_hash,
                        vector,
                        json.dumps(metadata),
                    ),
                )

    def touch_page(self, page_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE source_page SET last_seen_at=now(), deleted_at=NULL WHERE page_id=%s",
                (page_id,),
            )

    def tombstone_missing(self, space_id: str, seen_page_ids: set[str]) -> int:
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE source_page SET deleted_at=now()
                WHERE space_id=%s AND deleted_at IS NULL AND NOT (page_id = ANY(%s::text[]))
                """,
                (space_id, list(seen_page_ids)),
            )
            return result.rowcount

    def get_watermark(self, scope: str):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT last_modified_watermark FROM sync_cursor WHERE scope=%s", (scope,)
            ).fetchone()
            return row["last_modified_watermark"] if row else None

    def set_watermark(self, scope: str, watermark) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sync_cursor(scope,last_modified_watermark,last_success_at)
                VALUES (%s,%s,now())
                ON CONFLICT(scope) DO UPDATE SET
                  last_modified_watermark=EXCLUDED.last_modified_watermark,
                  last_success_at=now(), updated_at=now()
                """,
                (scope, watermark),
            )

    def start_ingestion_run(self, space_id: str, mode: str) -> UUID:
        run_id = uuid4()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_run(run_id, space_id, mode)
                VALUES (%s, %s, %s)
                """,
                (run_id, space_id, mode),
            )
        return run_id

    def finish_ingestion_run(
        self,
        run_id: UUID,
        *,
        status: str,
        pages_discovered: int,
        pages_embedded: int,
        chunks_embedded: int,
        pages_skipped: int,
        pages_tombstoned: int,
        error: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE ingestion_run AS run SET
                  completed_at=now(), status=%s, error=%s,
                  pages_discovered=%s, pages_embedded=%s, chunks_embedded=%s,
                  pages_skipped=%s, pages_tombstoned=%s,
                  total_pages=(
                    SELECT count(*) FROM source_page
                    WHERE space_id=run.space_id AND deleted_at IS NULL
                  ),
                  total_chunks=(
                    SELECT count(*) FROM knowledge_chunk AS chunk
                    JOIN source_page AS page ON page.page_id=chunk.page_id
                    WHERE page.space_id=run.space_id AND page.deleted_at IS NULL
                  ),
                  labelled_pages=(
                    SELECT count(*) FROM source_page
                    WHERE space_id=run.space_id AND deleted_at IS NULL
                      AND jsonb_array_length(COALESCE(metadata->'labels', '[]'::jsonb)) > 0
                  ),
                  distinct_labels=(
                    SELECT count(DISTINCT labels.value)
                    FROM source_page AS page
                    CROSS JOIN LATERAL jsonb_array_elements_text(
                      COALESCE(page.metadata->'labels', '[]'::jsonb)
                    ) AS labels(value)
                    WHERE page.space_id=run.space_id AND page.deleted_at IS NULL
                  )
                WHERE run_id=%s
                """,
                (
                    status,
                    error,
                    pages_discovered,
                    pages_embedded,
                    chunks_embedded,
                    pages_skipped,
                    pages_tombstoned,
                    run_id,
                ),
            )

    def ingestion_history(self, limit: int = 20) -> list[dict]:
        with self.connect() as connection:
            return connection.execute(
                """
                WITH history AS (
                  SELECT *,
                    total_pages - lag(total_pages) OVER (
                      PARTITION BY space_id ORDER BY started_at
                    ) AS page_delta,
                    total_chunks - lag(total_chunks) OVER (
                      PARTITION BY space_id ORDER BY started_at
                    ) AS chunk_delta
                  FROM ingestion_run
                )
                SELECT run_id, space_id, mode, started_at, completed_at, status,
                       pages_discovered, pages_embedded, chunks_embedded,
                       pages_skipped, pages_tombstoned, total_pages, total_chunks,
                       labelled_pages, distinct_labels, page_delta, chunk_delta, error
                FROM history
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()

    def search(self, query_vector: list[float], limit: int = 5) -> list[dict]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT c.content, c.metadata, c.page_id, c.chunk_index,
                       1 - (c.embedding <=> %s::vector) AS similarity
                FROM knowledge_chunk c
                JOIN source_page p ON p.page_id=c.page_id
                WHERE p.deleted_at IS NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (query_vector, query_vector, limit),
            ).fetchall()
