import httpx
import pytest

from knowledge_workflow.http_client import FetchError, SafeHttpClient


def test_client_preserves_conditional_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["if-none-match"] == '"abc"'
        return httpx.Response(304, headers={"etag": '"abc"'})

    with SafeHttpClient(
        allowed_hosts={"example.com"},
        transport=httpx.MockTransport(handler),
        sleeper=lambda _: None,
    ) as client:
        response = client.get("https://example.com/feed", etag='"abc"')

    assert response.not_modified


def test_client_blocks_redirect_to_unapproved_host() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://untrusted.example/payload"})

    with SafeHttpClient(
        allowed_hosts={"example.com"},
        max_retries=0,
        transport=httpx.MockTransport(handler),
        sleeper=lambda _: None,
    ) as client:
        with pytest.raises(FetchError, match="non-allowlisted"):
            client.get("https://example.com/feed")
