from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from urllib.parse import urljoin

import httpx

from knowledge_poc.models import SourcePage


class ConfluenceClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            auth=(email, api_token),
            headers={"Accept": "application/json"},
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
                yield page
            next_url = payload.get("_links", {}).get("next")
            url = urljoin(self.base_url, next_url) if next_url else ""
            params = None

    def _map_page(self, item: dict) -> SourcePage:
        version = item.get("version") or {}
        body = item.get("body") or {}
        storage = body.get("storage") or {}
        updated_at = datetime.fromisoformat(version["createdAt"].replace("Z", "+00:00"))
        webui = (item.get("_links") or {}).get("webui", "")
        # Confluence Cloud returns webui as /spaces/... while the browser route
        # lives below /wiki/. A leading slash passed directly to urljoin would
        # otherwise discard that prefix.
        webui_path = webui.removeprefix("/wiki/").lstrip("/")
        return SourcePage(
            page_id=str(item["id"]),
            space_id=str(item["spaceId"]),
            parent_id=str(item["parentId"]) if item.get("parentId") else None,
            title=item["title"],
            version=int(version["number"]),
            storage_html=storage.get("value", ""),
            source_url=urljoin(f"{self.base_url}/wiki/", webui_path),
            updated_at=updated_at,
            metadata={"status": item.get("status"), "subtype": item.get("subtype")},
        )
