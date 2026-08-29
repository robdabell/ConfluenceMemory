from knowledge_poc.embeddings.client import MockEmbeddings


def test_mock_embeddings_are_deterministic_and_normalized():
    model = MockEmbeddings(32)
    first = model.embed_query("offline vessel operations")
    second = model.embed_query("offline vessel operations")
    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 1e-9

