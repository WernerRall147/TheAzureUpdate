"""Safe text normalization helpers for external source content."""

from __future__ import annotations

import html
import re
from hashlib import sha256
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "form", "iframe", "svg"}:
            self._ignored_depth += 1
        elif not self._ignored_depth and tag.casefold() in {"p", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "form", "iframe", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def clean_text(value: str, *, max_chars: int = 1200) -> str:
    parser = _TextExtractor()
    parser.feed(html.unescape(value or ""))
    text = " ".join("".join(parser.parts).split())
    text = re.sub(r"The post .+? appeared first on .+?\.?$", "", text, flags=re.IGNORECASE)
    if len(text) <= max_chars:
        return text.strip()
    return f"{text[: max_chars - 3].rstrip()}..."


def clean_markdown(value: str, *, max_chars: int = 1200) -> str:
    text = re.sub(r"```.*?```", " ", value or "", flags=re.DOTALL)
    text = re.sub(r"!\[[^]]*]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*_`~-]+", " ", text)
    return clean_text(text, max_chars=max_chars)


def slugify(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:max_length].rstrip("-") or "item"


def stable_item_id(source_id: str, external_id: str, technology: str) -> str:
    suffix = slugify(external_id, max_length=40)
    if len(external_id) > 48 or "/" in external_id or ":" in external_id:
        suffix = sha256(external_id.encode("utf-8")).hexdigest()[:12]
    return f"{slugify(source_id, max_length=32)}-{technology}-{suffix}"
