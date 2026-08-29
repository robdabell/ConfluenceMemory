from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from knowledge_poc.models import TextChunk
from knowledge_poc.transformation.hashing import sha256_text


def chunk_page(page_id: str, text: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    parts = splitter.split_text(text)
    return [
        TextChunk(
            chunk_id=f"{page_id}:{index}:{sha256_text(content)[:12]}",
            page_id=page_id,
            chunk_index=index,
            content=content,
            content_hash=sha256_text(content),
        )
        for index, content in enumerate(parts)
    ]

