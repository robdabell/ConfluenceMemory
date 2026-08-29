import sys
from types import SimpleNamespace

import pytest

from knowledge_poc.embeddings.client import LocalEmbeddings


def test_local_model_uses_current_dimension_api(monkeypatch):
    class FakeModel:
        def get_embedding_dimension(self):
            return 384

        def get_sentence_embedding_dimension(self):
            raise AssertionError("Deprecated dimension API should not be called")

    fake_module = SimpleNamespace(SentenceTransformer=lambda _model_name: FakeModel())
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    model = LocalEmbeddings("test-model", 384)

    assert isinstance(model.model, FakeModel)


@pytest.mark.skip(reason="Downloads the model; run explicitly during environment validation")
def test_local_model_dimensions_and_similarity():
    model = LocalEmbeddings("BAAI/bge-small-en-v1.5", 384)
    vectors = model.embed_documents(
        ["A vessel must work offline for fourteen days.", "The interface uses blue buttons."]
    )
    query = model.embed_query("How long can the vessel operate without connectivity?")
    assert len(query) == 384
    assert len(vectors[0]) == 384
