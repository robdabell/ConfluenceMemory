CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_migration (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_page (
    page_id text PRIMARY KEY,
    space_id text NOT NULL,
    parent_id text,
    title text NOT NULL,
    version integer NOT NULL,
    content_hash text NOT NULL,
    structure_hash text NOT NULL,
    source_url text NOT NULL,
    updated_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS knowledge_chunk (
    chunk_id text PRIMARY KEY,
    page_id text NOT NULL REFERENCES source_page(page_id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    heading_path text,
    content text NOT NULL,
    content_hash text NOT NULL,
    embedding vector NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (page_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS knowledge_chunk_page_idx ON knowledge_chunk(page_id);

CREATE TABLE IF NOT EXISTS sync_cursor (
    scope text PRIMARY KEY,
    last_modified_watermark timestamptz,
    last_success_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestion_run (
    run_id uuid PRIMARY KEY,
    mode text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    pages_discovered integer NOT NULL DEFAULT 0,
    pages_embedded integer NOT NULL DEFAULT 0,
    chunks_embedded integer NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'running',
    error text
);

