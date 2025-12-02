from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def _request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> httpx.Response:
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    retries = 3
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    headers=merged_headers,
                )
                response.raise_for_status()
                return response
            except Exception as exc:  # pragma: no cover - exercised in integration
                last_exc = exc
                await asyncio.sleep(0.5 * (attempt + 1))
        assert last_exc is not None
        raise last_exc


async def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    response = await _request("GET", url, params=params, headers=headers, timeout=timeout)
    return response.json()


async def get_html(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> str:
    response = await _request("GET", url, params=params, headers=headers, timeout=timeout)
    return response.text
