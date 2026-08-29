import hashlib


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def structure_hash(title: str, parent_id: str | None, text: str) -> str:
    headings = "\n".join(line for line in text.splitlines() if line.startswith("#"))
    return sha256_text(f"{title}\n{parent_id or ''}\n{headings}")

