from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from urllib.parse import urljoin

import httpx

from knowledge_poc.models import SourcePage


class ConfluenceClient:
    def __init__(
        self,
        base_url: str,
        email: str | None = None,
        api_token: str | None = None,
        timeout: float = 30.0,
        *,
        access_token: str | None = None,
        site_url: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.site_url = (site_url or base_url).rstrip("/")
        if client:
            self.client = client
        else:
            headers = {"Accept": "application/json"}
            auth = None
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            else:
                if not email or not api_token:
                    raise ValueError("Basic auth requires both email and API token")
                auth = (email, api_token)
            self.client = httpx.Client(auth=auth, headers=headers, timeout=timeout)

    @classmethod
    def oauth(
        cls, cloud_id: str, access_token: str, site_url: str, timeout: float = 30.0
    ) -> ConfluenceClient:
        return cls(
            f"https://api.atlassian.com/ex/confluence/{cloud_id}",
            access_token=access_token,
            site_url=site_url,
            timeout=timeout,
        )

    def close(self) -> None:
        self.client.close()

    def iter_pages(self, space_id: str, since: datetime | None = None) -> Iterator[SourcePage]:
        url = f"{self.base_url}/wiki/api/v2/spaces/{space_id}/pages"
        params: dict[str, str | int] | None = {
            "body-format": "storage",
            "sort": "-modified-date",
            "status": "current",
            "limit": 100,
        }
        while url:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("results", []):
                page = self._map_page(item)
                if since and page.updated_at <= since:
                    return
                yield replace(
                    page,
                    metadata={**page.metadata, "labels": self.get_page_labels(page.page_id)},
                )
            next_url = self._next_link(response, payload)
            url = self._api_url(next_url) if next_url else ""
            params = None

    def iter_page_summaries(self, space_id: str) -> Iterator[dict]:
        """List current pages without requesting their bodies."""
        url = f"{self.base_url}/wiki/api/v2/spaces/{space_id}/pages"
        params: dict[str, str | int] | None = {
            "sort": "title",
            "status": "current",
            "limit": 100,
        }
        while url:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("results", []):
                version = item.get("version") or {}
                yield {
                    "id": str(item["id"]),
                    "space_id": str(item["spaceId"]),
                    "parent_id": str(item["parentId"]) if item.get("parentId") else None,
                    "title": item["title"],
                    "status": item.get("status"),
                    "version": int(version["number"]) if version.get("number") else None,
                    "updated_at": version.get("createdAt"),
                    "url": self._page_url(item),
                }
            next_url = self._next_link(response, payload)
            url = self._api_url(next_url) if next_url else ""
            params = None

    def get_page_labels(self, page_id: str) -> list[str]:
        """Return every visible label for a page using GET requests only."""
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}/labels"
        params: dict[str, str | int] | None = {"limit": 250}
        labels: set[str] = set()
        while url:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            labels.update(
                str(item["name"])
                for item in payload.get("results", [])
                if item.get("name")
            )
            next_url = self._next_link(response, payload)
            url = self._api_url(next_url) if next_url else ""
            params = None
        return sorted(labels)

    def get_space_by_key(self, space_key: str) -> dict:
        response = self.client.get(
            f"{self.base_url}/wiki/api/v2/spaces",
            params={"keys": space_key, "limit": 1},
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        matches = [item for item in results if item.get("key") == space_key]
        if not matches:
            raise ValueError(f"Confluence space {space_key!r} was not found or is not accessible")
        return matches[0]

    def get_first_page(self, space_id: str) -> SourcePage | None:
        response = self.client.get(
            f"{self.base_url}/wiki/api/v2/spaces/{space_id}/pages",
            params={"body-format": "storage", "status": "current", "limit": 1},
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return self._map_page(results[0]) if results else None

    def _map_page(self, item: dict) -> SourcePage:
        version = item.get("version") or {}
        body = item.get("body") or {}
        storage = body.get("storage") or {}
        updated_at = datetime.fromisoformat(version["createdAt"].replace("Z", "+00:00"))
        return SourcePage(
            page_id=str(item["id"]),
            space_id=str(item["spaceId"]),
            parent_id=str(item["parentId"]) if item.get("parentId") else None,
            title=item["title"],
            version=int(version["number"]),
            storage_html=storage.get("value", ""),
            source_url=self._page_url(item),
            updated_at=updated_at,
            metadata={
                "status": item.get("status"),
                "subtype": item.get("subtype"),
                "labels": sorted(
                    str(label["name"])
                    for label in (item.get("labels") or {}).get("results", [])
                    if label.get("name")
                ),
            },
        )

    def _api_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        api_path = path.removeprefix("/wiki/").lstrip("/")
        return urljoin(f"{self.base_url}/wiki/", api_path)

    @staticmethod
    def _next_link(response: httpx.Response, payload: dict) -> str | None:
        body_link = payload.get("_links", {}).get("next")
        header_link = response.links.get("next", {}).get("url")
        return body_link or header_link

    def _page_url(self, item: dict) -> str:
        webui = (item.get("_links") or {}).get("webui", "")
        # Confluence Cloud returns webui as /spaces/... while the browser route
        # lives below /wiki/. A leading slash passed directly to urljoin would
        # otherwise discard that prefix.
        webui_path = webui.removeprefix("/wiki/").lstrip("/")
        return urljoin(f"{self.site_url}/wiki/", webui_path)
