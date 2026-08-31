import json
from pathlib import Path

import httpx

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


def test_oauth_probe_operations_are_get_only_and_use_gateway():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/spaces"):
            return httpx.Response(200, json={"results": [{"id": "42", "key": "S3CR"}]})
        return httpx.Response(200, json={"results": []})

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer token"},
    ) as http_client:
        client = ConfluenceClient(
            "https://api.atlassian.com/ex/confluence/cloud-id",
            site_url="https://vstaging.atlassian.net",
            client=http_client,
        )
        space = client.get_space_by_key("S3CR")
        page = client.get_first_page(space["id"])

    assert page is None
    assert [request.method for request in requests] == ["GET", "GET"]
    assert all(
        request.url.host == "api.atlassian.com"
        and request.url.path.startswith("/ex/confluence/cloud-id/wiki/api/v2/")
        for request in requests
    )
