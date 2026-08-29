import pytest

from knowledge_poc.embeddings.client import LocalEmbeddings


@pytest.mark.skip(reason="Downloads the model; run explicitly during environment validation")
def test_local_model_dimensions_and_similarity():
    model = LocalEmbeddings("BAAI/bge-small-en-v1.5", 384)
    vectors = model.embed_documents(
        ["A vessel must work offline for fourteen days.", "The interface uses blue buttons."]
    )
    query = model.embed_query("How long can the vessel operate without connectivity?")
    assert len(query) == 384
    assert len(vectors[0]) == 384

