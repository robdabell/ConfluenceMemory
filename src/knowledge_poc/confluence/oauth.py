from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

AUTHORIZE_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
READ_SCOPES = ("read:page:confluence", "read:space:confluence")


@dataclass(frozen=True)
class OAuthCredentials:
    access_token: str
    cloud_id: str
    site_url: str


def authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    query = urlencode(
        {
            "audience": "api.atlassian.com",
            "client_id": client_id,
            "scope": " ".join(READ_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def _callback_result(path: str, expected_path: str, expected_state: str) -> tuple[str, str]:
    parsed = urlparse(path)
    if parsed.path != expected_path:
        raise ValueError("Unexpected OAuth callback path")
    query = parse_qs(parsed.query)
    if query.get("state", [None])[0] != expected_state:
        raise ValueError("OAuth state mismatch")
    if error := query.get("error", [None])[0]:
        description = query.get("error_description", [error])[0]
        raise ValueError(f"Atlassian authorization failed: {description}")
    code = query.get("code", [None])[0]
    if not code:
        raise ValueError("OAuth callback did not include an authorization code")
    return code, "Authorization received. You can close this tab."


def wait_for_authorization_code(
    redirect_uri: str, expected_state: str, timeout_seconds: int = 300
) -> str:
    redirect = urlparse(redirect_uri)
    if redirect.scheme != "http" or redirect.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("The PoC callback must be an http://localhost or 127.0.0.1 URL")
    if not redirect.port:
        raise ValueError("ATLASSIAN_REDIRECT_URI must include a callback port")

    result: dict[str, str | Exception] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            status = 200
            try:
                code, message = _callback_result(self.path, redirect.path, expected_state)
                result["code"] = code
            except ValueError as exc:
                status = 400
                message = str(exc)
                result["error"] = exc
            body = message.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = HTTPServer(("0.0.0.0", redirect.port), CallbackHandler)
    server.timeout = timeout_seconds
    server.handle_request()
    server.server_close()
    if error := result.get("error"):
        raise error
    if code := result.get("code"):
        return str(code)
    raise TimeoutError(f"No OAuth callback received within {timeout_seconds} seconds")


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    client: httpx.Client | None = None,
) -> str:
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        response = client.post(
            TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("Atlassian token response did not include an access token")
        return str(token)
    finally:
        if owns_client:
            client.close()


def resolve_cloud_resource(
    access_token: str, site_url: str, client: httpx.Client | None = None
) -> tuple[str, str]:
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        response = client.get(
            RESOURCES_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        response.raise_for_status()
        expected = site_url.rstrip("/").casefold()
        matches = [
            resource
            for resource in response.json()
            if str(resource.get("url", "")).rstrip("/").casefold() == expected
        ]
        if not matches:
            raise ValueError(f"The authorization did not grant access to {site_url}")
        return str(matches[0]["id"]), str(matches[0]["url"]).rstrip("/")
    finally:
        if owns_client:
            client.close()


def authenticate(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    site_url: str,
    echo: Callable[[str], object],
    timeout_seconds: int = 300,
) -> OAuthCredentials:
    state = secrets.token_urlsafe(32)
    echo("Open this URL in your browser and sign in through your organisation's Entra SSO:")
    echo(authorization_url(client_id, redirect_uri, state))
    code = wait_for_authorization_code(redirect_uri, state, timeout_seconds)
    access_token = exchange_code(client_id, client_secret, code, redirect_uri)
    cloud_id, resolved_site_url = resolve_cloud_resource(access_token, site_url)
    return OAuthCredentials(access_token, cloud_id, resolved_site_url)
