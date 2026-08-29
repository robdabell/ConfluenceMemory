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
