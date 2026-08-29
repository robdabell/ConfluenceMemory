import json
from pathlib import Path

from knowledge_poc.confluence.client import ConfluenceClient


def test_page_url_keeps_confluence_wiki_prefix():
    fixture = Path("tests/fixtures/confluence_pages.json")
    item = json.loads(fixture.read_text(encoding="utf-8"))["results"][0]
    client = ConfluenceClient("https://example.atlassian.net", "user@example.com", "token")
    try:
        page = client._map_page(item)
    finally:
        client.close()

    assert page.source_url == (
        "https://example.atlassian.net/wiki/spaces/ARCH/pages/123456"
    )


def test_page_url_does_not_duplicate_existing_wiki_prefix():
    item = {
        "id": "1",
        "spaceId": "2",
        "title": "Page",
        "version": {"number": 1, "createdAt": "2026-08-29T08:00:00Z"},
        "body": {"storage": {"value": "<p>Body</p>"}},
        "_links": {"webui": "/wiki/spaces/SPACE/pages/1"},
    }
    client = ConfluenceClient("https://example.atlassian.net", "user@example.com", "token")
    try:
        page = client._map_page(item)
    finally:
        client.close()

    assert page.source_url == "https://example.atlassian.net/wiki/spaces/SPACE/pages/1"
