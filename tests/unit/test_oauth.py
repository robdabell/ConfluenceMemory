from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from knowledge_poc.confluence.oauth import (
    READ_SCOPES,
    _callback_result,
    authorization_url,
    exchange_code,
    resolve_cloud_resource,
)


def test_authorization_url_requests_only_read_scopes_and_no_offline_access():
    url = authorization_url("client-id", "http://localhost:8765/callback", "state-value")
    query = parse_qs(urlparse(url).query)

    assert query["scope"] == [" ".join(READ_SCOPES)]
    assert "offline_access" not in query["scope"][0]
    assert query["state"] == ["state-value"]
    assert query["response_type"] == ["code"]


def test_callback_rejects_state_mismatch():
    with pytest.raises(ValueError, match="state mismatch"):
        _callback_result("/callback?code=secret&state=wrong", "/callback", "expected")


def test_exchange_code_uses_token_endpoint_without_persisting_token():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["request"] = request
        return httpx.Response(200, json={"access_token": "memory-only-token"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        token = exchange_code(
            "client-id", "client-secret", "code", "http://localhost:8765/callback", client
        )

    assert token == "memory-only-token"
    assert seen["request"].url == "https://auth.atlassian.com/oauth/token"
    assert seen["request"].method == "POST"


def test_resolve_cloud_resource_matches_configured_site():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json=[
                {"id": "other", "url": "https://other.atlassian.net"},
                {"id": "cloud-id", "url": "https://vstaging.atlassian.net/"},
            ],
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = resolve_cloud_resource("token", "https://vstaging.atlassian.net", client)

    assert result == ("cloud-id", "https://vstaging.atlassian.net")
