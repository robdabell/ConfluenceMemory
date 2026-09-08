from datetime import UTC, datetime

import pytest

from knowledge_poc.ingestion.sync import Synchroniser
from knowledge_poc.models import SourcePage


class FakeDatabase:
    def __init__(self):
        self.finished = []
        self.replaced = []

    def get_watermark(self, _scope):
        return None

    def start_ingestion_run(self, space_id, mode):
        assert (space_id, mode) == ("42", "full")
        return "run-id"

    def get_page_state(self, _page_id):
        return None

    def replace_page(self, *args):
        self.replaced.append(args)

    def tombstone_missing(self, _space_id, _seen):
        return 0

    def set_watermark(self, _scope, _watermark):
        return None

    def finish_ingestion_run(self, run_id, **values):
        self.finished.append((run_id, values))


class FakeEmbeddings:
    def __init__(self):
        self.texts = []

    def embed_documents(self, texts):
        self.texts.extend(texts)
        return [[0.0, 1.0] for _text in texts]


def sample_page():
    return SourcePage(
        page_id="1",
        space_id="42",
        parent_id=None,
        title="Offline requirements",
        version=1,
        storage_html="<p>A vessel must operate offline.</p>",
        source_url="https://example.atlassian.net/wiki/pages/1",
        updated_at=datetime(2026, 9, 8, tzinfo=UTC),
        metadata={"labels": ["offline", "vessel"]},
    )


def test_ingestion_records_completed_run_and_embeds_label_context():
    database = FakeDatabase()
    embeddings = FakeEmbeddings()
    confluence = type("Confluence", (), {"iter_pages": lambda *_args, **_kwargs: [sample_page()]})()
    synchroniser = Synchroniser(confluence, database, embeddings, 1000, 150)

    result = synchroniser.run("42", full=True)

    assert result.discovered == 1
    assert embeddings.texts[0].startswith("Labels: offline, vessel\n\n")
    assert database.finished[0][0] == "run-id"
    assert database.finished[0][1]["status"] == "completed"
    assert database.finished[0][1]["pages_discovered"] == 1


def test_ingestion_records_failed_run():
    database = FakeDatabase()

    class FailingConfluence:
        def iter_pages(self, *_args, **_kwargs):
            raise RuntimeError("upstream unavailable")

    synchroniser = Synchroniser(FailingConfluence(), database, FakeEmbeddings(), 1000, 150)

    with pytest.raises(RuntimeError, match="upstream unavailable"):
        synchroniser.run("42", full=True)

    assert database.finished[0][1]["status"] == "failed"
    assert database.finished[0][1]["error"] == "upstream unavailable"
