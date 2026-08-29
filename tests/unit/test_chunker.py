from knowledge_poc.transformation.chunker import chunk_page


def test_chunk_ids_are_deterministic():
    first = chunk_page("42", "# Title\n\n" + "word " * 100, 100, 10)
    second = chunk_page("42", "# Title\n\n" + "word " * 100, 100, 10)
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert len(first) > 1

