ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS space_id text;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS pages_skipped integer NOT NULL DEFAULT 0;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS pages_tombstoned integer NOT NULL DEFAULT 0;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS total_pages integer;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS total_chunks integer;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS labelled_pages integer;
ALTER TABLE ingestion_run ADD COLUMN IF NOT EXISTS distinct_labels integer;

CREATE INDEX IF NOT EXISTS ingestion_run_space_started_idx
    ON ingestion_run(space_id, started_at DESC);
