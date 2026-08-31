from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import typer

from knowledge_poc.config import Settings
from knowledge_poc.confluence.client import ConfluenceClient
from knowledge_poc.confluence.oauth import authenticate
from knowledge_poc.embeddings.client import Embeddings, create_embeddings
from knowledge_poc.ingestion.sync import Synchroniser
from knowledge_poc.storage.database import Database

app = typer.Typer(help="Confluence to pgvector knowledge PoC")


def _database(settings: Settings) -> Database:
    return Database(settings.database_url)


def _run_sync(
    settings: Settings, client: ConfluenceClient, embeddings: Embeddings, full: bool
) -> None:
    result = Synchroniser(
        client,
        _database(settings),
        embeddings,
        settings.chunk_size,
        settings.chunk_overlap,
    ).run(settings.confluence_space_id or "", full=full)
    typer.echo(json.dumps(result.__dict__, indent=2))


def _sync_once(full: bool) -> None:
    settings = Settings.from_env(require_confluence=True)
    embeddings = create_embeddings(
        settings.embedding_provider, settings.embedding_model, settings.embedding_dimensions
    )
    client = ConfluenceClient(
        settings.confluence_base_url or "",
        settings.confluence_email or "",
        settings.confluence_api_token or "",
    )
    try:
        _run_sync(settings, client, embeddings, full)
    finally:
        client.close()


@app.command()
def migrate() -> None:
    """Apply SQL migrations."""
    settings = Settings.from_env()
    migrations_dir = (
        Path("/app/migrations") if Path("/app/migrations").exists() else Path("migrations")
    )
    for migration in _database(settings).migrate(migrations_dir):
        typer.echo(f"Applied {migration}")


@app.command()
def sync(full: bool = typer.Option(False, "--full", help="Also detect deleted pages")) -> None:
    """Run one Confluence synchronization."""
    _sync_once(full)


@app.command()
def poll() -> None:
    """Run incremental synchronization continuously."""
    settings = Settings.from_env(require_confluence=True)
    embeddings = create_embeddings(
        settings.embedding_provider, settings.embedding_model, settings.embedding_dimensions
    )
    client = ConfluenceClient(
        settings.confluence_base_url or "",
        settings.confluence_email or "",
        settings.confluence_api_token or "",
    )
    try:
        while True:
            try:
                _run_sync(settings, client, embeddings, full=False)
            except Exception:
                logging.exception("Synchronization failed; the watermark was not advanced")
            time.sleep(settings.poll_interval_seconds)
    finally:
        client.close()


@app.command()
def search(question: str, limit: int = typer.Option(5, min=1, max=20)) -> None:
    """Embed a question and return the nearest cited chunks."""
    settings = Settings.from_env()
    embeddings = create_embeddings(
        settings.embedding_provider, settings.embedding_model, settings.embedding_dimensions
    )
    rows = _database(settings).search(embeddings.embed_query(question), limit)
    typer.echo(json.dumps(rows, indent=2, default=str))


@app.command()
def probe(timeout: int = typer.Option(300, min=30, max=900)) -> None:
    """Authenticate interactively and GET one page; never write to Confluence or PostgreSQL."""
    settings = Settings.from_env(require_oauth=True)
    credentials = authenticate(
        settings.atlassian_client_id or "",
        settings.atlassian_client_secret or "",
        settings.atlassian_redirect_uri,
        settings.confluence_base_url or "",
        typer.echo,
        timeout,
    )
    client = ConfluenceClient.oauth(
        credentials.cloud_id, credentials.access_token, credentials.site_url
    )
    try:
        space = client.get_space_by_key(settings.confluence_space_key or "")
        page = client.get_first_page(str(space["id"]))
    finally:
        client.close()
    result = {
        "site": credentials.site_url,
        "space": {"id": str(space["id"]), "key": space.get("key"), "name": space.get("name")},
        "page": (
            {
                "id": page.page_id,
                "title": page.title,
                "version": page.version,
                "url": page.source_url,
                "body_characters_read": len(page.storage_html),
            }
            if page
            else None
        ),
        "writes_performed": 0,
        "token_persisted": False,
    }
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
