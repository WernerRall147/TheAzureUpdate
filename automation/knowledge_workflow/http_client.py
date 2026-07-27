"""Allowlisted HTTP fetching with conditional requests and bounded retries."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

import httpx


LOGGER = logging.getLogger(__name__)
REDIRECT_CODES = {301, 302, 303, 307, 308}
TRANSIENT_CODES = {408, 425, 429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """Raised when a source cannot be fetched safely or reliably."""


@dataclass(slots=True, frozen=True)
class FetchResponse:
    status_code: int
    content: bytes
    url: str
    etag: str | None
    last_modified: str | None

    @property
    def not_modified(self) -> bool:
        return self.status_code == 304


class SafeHttpClient:
    def __init__(
        self,
        *,
        allowed_hosts: set[str] | frozenset[str],
        timeout_seconds: float = 30,
        max_retries: int = 3,
        token: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.allowed_hosts = {host.casefold() for host in allowed_hosts}
        self.max_retries = max_retries
        self.sleeper = sleeper
        headers = {
            "Accept": "application/json, application/atom+xml, application/rss+xml, text/xml, */*",
            "User-Agent": "csa-technology-knowledge/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=False,
            headers=headers,
            transport=transport,
        )

    def __enter__(self) -> "SafeHttpClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.client.close()

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").casefold()
        if parsed.scheme != "https" or host not in self.allowed_hosts:
            raise FetchError(f"refusing non-allowlisted URL: {url}")

    def get(
        self,
        url: str,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> FetchResponse:
        self._validate_url(url)
        request_headers = dict(headers or {})
        if etag:
            request_headers["If-None-Match"] = etag
        if last_modified:
            request_headers["If-Modified-Since"] = last_modified

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            current_url = url
            try:
                for _ in range(6):
                    self._validate_url(current_url)
                    response = self.client.get(current_url, headers=request_headers)
                    if response.status_code not in REDIRECT_CODES:
                        break
                    location = response.headers.get("location")
                    if not location:
                        raise FetchError(f"redirect from {current_url} has no location")
                    current_url = urljoin(current_url, location)
                else:
                    raise FetchError(f"too many redirects while fetching {url}")

                if response.status_code in TRANSIENT_CODES:
                    raise FetchError(f"transient HTTP {response.status_code} for {current_url}")
                if response.status_code not in {200, 304}:
                    raise FetchError(f"HTTP {response.status_code} for {current_url}")

                return FetchResponse(
                    status_code=response.status_code,
                    content=response.content,
                    url=str(response.url),
                    etag=response.headers.get("etag"),
                    last_modified=response.headers.get("last-modified"),
                )
            except (httpx.HTTPError, FetchError) as error:
                last_error = error
                if attempt >= self.max_retries:
                    break
                delay = min(2**attempt, 8)
                LOGGER.warning("Fetch attempt %s failed for %s: %s", attempt + 1, url, error)
                self.sleeper(delay)

        raise FetchError(f"failed to fetch {url}: {last_error}") from last_error


def json_payload(response: FetchResponse) -> Any:
    try:
        return httpx.Response(200, content=response.content).json()
    except ValueError as error:
        raise FetchError(f"invalid JSON from {response.url}") from error
