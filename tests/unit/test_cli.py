from types import SimpleNamespace

import pytest

from knowledge_poc import cli


class StopPolling(Exception):
    pass


def test_poller_reuses_embedding_model_and_client(monkeypatch):
    settings = SimpleNamespace(
        embedding_provider="local",
        embedding_model="model",
        embedding_dimensions=384,
        confluence_base_url="https://example.atlassian.net",
        confluence_email="user@example.com",
        confluence_api_token="token",
        poll_interval_seconds=300,
    )
    embeddings = object()
    client = SimpleNamespace(close=lambda: None)
    calls = {"embeddings": 0, "client": 0, "sync": 0}

    monkeypatch.setattr(cli.Settings, "from_env", lambda **_kwargs: settings)

    def create_embeddings(*_args):
        calls["embeddings"] += 1
        return embeddings

    def create_client(*_args):
        calls["client"] += 1
        return client

    def run_sync(actual_settings, actual_client, actual_embeddings, full):
        assert (actual_settings, actual_client, actual_embeddings, full) == (
            settings,
            client,
            embeddings,
            False,
        )
        calls["sync"] += 1

    monkeypatch.setattr(cli, "create_embeddings", create_embeddings)
    monkeypatch.setattr(cli, "ConfluenceClient", create_client)
    monkeypatch.setattr(cli, "_run_sync", run_sync)
    monkeypatch.setattr(cli.time, "sleep", lambda _seconds: (_ for _ in ()).throw(StopPolling))

    with pytest.raises(StopPolling):
        cli.poll()

    assert calls == {"embeddings": 1, "client": 1, "sync": 1}


def test_probe_never_opens_database(monkeypatch):
    settings = SimpleNamespace(
        atlassian_client_id="client-id",
        atlassian_client_secret="client-secret",
        atlassian_redirect_uri="http://localhost:8765/callback",
        confluence_base_url="https://vstaging.atlassian.net",
        confluence_space_key="S3CR",
    )
    credentials = SimpleNamespace(
        access_token="memory-only-token",
        cloud_id="cloud-id",
        site_url="https://vstaging.atlassian.net",
    )
    client = SimpleNamespace(
        get_space_by_key=lambda key: {"id": "42", "key": key, "name": "Clean room"},
        get_first_page=lambda _space_id: None,
        close=lambda: None,
    )
    output: list[str] = []

    monkeypatch.setattr(cli.Settings, "from_env", lambda **_kwargs: settings)
    monkeypatch.setattr(cli, "authenticate", lambda *_args: credentials)
    monkeypatch.setattr(cli.ConfluenceClient, "oauth", lambda *_args: client)
    monkeypatch.setattr(
        cli, "_database", lambda *_args: pytest.fail("probe must not open PostgreSQL")
    )
    monkeypatch.setattr(cli.typer, "echo", lambda message: output.append(str(message)))

    cli.probe(timeout=30)

    assert '"writes_performed": 0' in output[-1]
    assert '"token_persisted": false' in output[-1]


def test_inspect_never_opens_database_or_reads_page_bodies(monkeypatch):
    settings = SimpleNamespace()
    credentials = SimpleNamespace(site_url="https://vstaging.atlassian.net")
    client = SimpleNamespace(
        iter_page_summaries=lambda _space_id: iter([{"id": "1", "title": "Page"}]),
        close=lambda: None,
    )
    space = {"id": "42", "key": "S3CR", "name": "Clean room"}
    output: list[str] = []

    monkeypatch.setattr(cli.Settings, "from_env", lambda **_kwargs: settings)
    monkeypatch.setattr(cli, "_oauth_context", lambda *_args: (credentials, client, space))
    monkeypatch.setattr(
        cli, "_database", lambda *_args: pytest.fail("inspect must not open PostgreSQL")
    )
    monkeypatch.setattr(cli.typer, "echo", lambda message: output.append(str(message)))

    cli.inspect_space(timeout=30)

    assert '"page_count": 1' in output[-1]
    assert '"page_bodies_read": 0' in output[-1]
    assert '"postgresql_opened": false' in output[-1]


def test_oauth_sync_uses_resolved_space_id(monkeypatch):
    settings = SimpleNamespace(
        embedding_provider="mock",
        embedding_model="model",
        embedding_dimensions=64,
    )
    credentials = SimpleNamespace(site_url="https://vstaging.atlassian.net")
    client = SimpleNamespace(close=lambda: None)
    space = {"id": "42", "key": "S3CR", "name": "Clean room"}
    embeddings = object()
    calls: list[tuple] = []

    monkeypatch.setattr(cli.Settings, "from_env", lambda **_kwargs: settings)
    monkeypatch.setattr(cli, "_oauth_context", lambda *_args: (credentials, client, space))
    monkeypatch.setattr(cli, "create_embeddings", lambda *_args: embeddings)
    monkeypatch.setattr(cli.typer, "echo", lambda _message: None)
    monkeypatch.setattr(
        cli,
        "_run_sync",
        lambda *args, **kwargs: calls.append((*args, kwargs)),
    )

    cli.oauth_sync(full=True, timeout=30)

    assert calls == [(settings, client, embeddings, True, {"space_id": "42"})]
