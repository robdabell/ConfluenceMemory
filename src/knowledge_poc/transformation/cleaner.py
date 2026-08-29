from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag


def clean_storage_html(storage_html: str, title: str) -> str:
    """Convert Confluence storage HTML into stable, readable text."""
    soup = BeautifulSoup(storage_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(heading.name[1])
        heading.insert_before(NavigableString(f"\n{'#' * level} "))
        heading.append(NavigableString("\n"))
    for li in soup.find_all("li"):
        li.insert_before(NavigableString("\n- "))
    for row in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
        if cells:
            row.replace_with(NavigableString("\n| " + " | ".join(cells) + " |\n"))
    for block in soup.find_all(["p", "div", "section", "pre"]):
        if isinstance(block, Tag):
            block.append(NavigableString("\n"))
    text = soup.get_text(" ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return f"# {title}\n\n{text}" if text else f"# {title}"

