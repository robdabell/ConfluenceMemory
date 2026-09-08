# Confluence Knowledge PoC

A standalone proof of concept for synchronising an approved Confluence Cloud space through the regular REST API into PostgreSQL + pgvector. It deliberately excludes Forge, Rovo, Teamwork Graph, LangGraph, and the current production vector store.

## What this proves

- Full and incremental Confluence polling
- Stable cleaning, chunking, and content hashing
- No embedding call for unchanged content
- Atomic replacement of all chunks for a changed page
- Tombstoning pages missing during a full reconciliation
- Question embedding and cited pgvector similarity search
- One Python image reused for migration, polling, and CLI commands

`EMBEDDING_PROVIDER=local` is the default. It uses `BAAI/bge-small-en-v1.5` through Sentence Transformers, producing meaningful 384-dimensional vectors without a paid embedding API. The first run downloads the model into a persistent Docker volume. `mock` remains available for fast plumbing tests, and `openai` is available when an exact comparison requires it.

## Quick start

```bash
cp .env.example .env
# Add the Confluence URL, account email, API token, and numeric space ID.

docker compose up -d postgres
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm cli sync --full
docker compose --profile tools run --rm cli search "How long must a vessel operate offline?"
```

## Interactive Entra-backed access (no API token)

Atlassian OAuth 2.0 (3LO) delegates sign-in to the organisation's configured Entra SSO.
The application never receives the user's Microsoft password. Create an OAuth integration in
the Atlassian Developer Console with callback URL `http://localhost:8765/callback`, grant only
`read:page:confluence` and `read:space:confluence`, then add its client ID and secret to `.env`.

Run the deliberately isolated read-only probe:

```bash
docker compose --profile tools run --rm --service-ports oauth-probe
```

Open the printed URL, sign in, and consent. The probe resolves `S3CR` and reads one page using
GET requests only. It does not start ingestion, open PostgreSQL, persist the access token, or
request offline access. Do not run `sync` or `poll` until this output has been reviewed.

Inventory every current page without requesting page bodies or opening PostgreSQL:

```bash
docker compose --profile tools run --rm --service-ports oauth-probe inspect
```

After reviewing that inventory, run one full OAuth ingestion. Confluence access remains GET-only;
the command writes embeddings and source metadata only to the local PostgreSQL container:

```bash
docker compose up -d postgres
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm --service-ports oauth-probe oauth-sync --full
```

The unattended `poll` command intentionally remains Basic-Auth-only. Do not use it with this
interactive, memory-only OAuth configuration.

Run continuous five-minute polling:

```bash
docker compose up -d poller
docker compose logs -f poller
```

## Embedding configuration

Local retrieval evaluation (default):

```dotenv
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSIONS=384
```

Fast synthetic plumbing test only:

```dotenv
EMBEDDING_PROVIDER=mock
EMBEDDING_DIMENSIONS=64
```

Relevance test using OpenAI:

```dotenv
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
OPENAI_API_KEY=...
```

Do not mix dimensions or models in one database. If the model changes during the PoC, recreate the disposable volume with `docker compose down -v` and ingest again.

## Sync behavior

Incremental sync reads the stored watermark with a five-minute overlap. Page and structure hashes make repeated pages cheap. The watermark advances only after the run completes. A full sync also marks pages no longer returned by Confluence as deleted, which removes them from retrieval without destroying audit state.

Every synchronization is recorded with its outcome, page/chunk changes, and a post-run
snapshot of available pages, chunks, labelled pages, and distinct labels. Compare runs with:

```bash
docker compose --profile tools run --rm cli ingestion-history --limit 20
```

Confluence page labels are fetched with GET requests, stored on page and chunk metadata,
and included as context when creating embeddings. Run a full synchronization to reconcile
labels for pages already in the local corpus.

For a real evaluation, schedule incremental polling every five minutes and a full reconciliation nightly.

## Security boundary

The PoC integration account can only ingest pages it can view. That is adequate for a bounded, commonly approved test space. It is not yet delegated user authorization. Do not include mixed-access production spaces until page restrictions and requesting-user access checks are implemented and tested.

## Tests

For a local Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check src tests
```

The mock embedding provider makes unit and plumbing tests repeatable and free. The local model supports meaningful no-cost user testing. For a strictly controlled comparison with the current implementation, either use its same embedding model or clearly record the local model as an experimental variable.

## Next slice

1. Add mocked Confluence HTTP integration tests.
2. Add per-page failure details to the ingestion run log.
3. Add PostgreSQL advisory locking for overlapping pollers.
4. Add golden-question Recall@5 evaluation.
5. Add a small user-test UI only after the ingestion lifecycle is stable.

## Current deliberate limitations

- One configured numeric Confluence space ID
- Basic auth remains available for unattended polling; the read-only probe supports interactive OAuth
- Whole-page chunk replacement rather than chunk-level differential updates
- No attachment extraction
- No page/space ACL replication or delegated access check
- Brute-force vector search (appropriate for the small PoC corpus)
