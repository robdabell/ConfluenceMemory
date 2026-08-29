from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class Embeddings(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class MockEmbeddings:
    """Deterministic local feature hashing for plumbing tests, not relevance evaluation."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class LocalEmbeddings:
    """Sentence Transformers running locally on CPU, GPU, or Apple MPS."""

    def __init__(self, model_name: str, expected_dimensions: int):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        if hasattr(self.model, "get_embedding_dimension"):
            actual = self.model.get_embedding_dimension()
        else:
            actual = self.model.get_sentence_embedding_dimension()
        if actual != expected_dimensions:
            raise ValueError(
                f"Model {model_name} produces {actual} dimensions, "
                f"but EMBEDDING_DIMENSIONS={expected_dimensions}"
            )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode_document(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode_query(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vector.tolist()


def create_embeddings(provider: str, model: str, dimensions: int) -> Embeddings:
    if provider == "mock":
        return MockEmbeddings(dimensions)
    if provider == "local":
        return LocalEmbeddings(model, dimensions)
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=model, dimensions=dimensions)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
