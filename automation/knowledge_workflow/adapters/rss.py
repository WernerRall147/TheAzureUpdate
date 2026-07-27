"""RSS 2.0 and Atom feed parsing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

from ..models import KnowledgeItem
from ..text import clean_text
from .common import build_item


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def _children(node: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in node if _local_name(child.tag) == name.casefold()]


def _text(node: ElementTree.Element, *names: str) -> str:
    for name in names:
        matches = _children(node, name)
        if matches and matches[0].text:
            return matches[0].text.strip()
    return ""


def _link(node: ElementTree.Element) -> str:
    for child in _children(node, "link"):
        if child.get("href") and child.get("rel", "alternate") in {"alternate", ""}:
            return str(child.get("href"))
        if child.text:
            return child.text.strip()
    return ""


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _resolve_technologies(source: dict[str, Any], categories: list[str]) -> list[str]:
    fixed = source.get("technology")
    if fixed:
        return [str(fixed)]
    category_map = {str(key).casefold(): str(value) for key, value in source.get("category_map", {}).items()}
    return sorted({category_map[category.casefold()] for category in categories if category.casefold() in category_map})


def parse_feed(
    payload: str | bytes,
    source: dict[str, Any],
    *,
    observed_at: datetime,
) -> list[KnowledgeItem]:
    root = ElementTree.fromstring(payload)
    entries = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    max_items = int(source.get("max_items", 25))
    since_days = int(source.get("since_days", 21))
    cutoff = observed_at - timedelta(days=since_days)
    output: list[KnowledgeItem] = []

    for entry in entries:
        title = clean_text(_text(entry, "title"), max_chars=300)
        source_url = _link(entry)
        external_id = _text(entry, "guid", "id") or source_url
        published_at = _parse_date(_text(entry, "pubdate", "published", "updated"))
        if published_at and published_at < cutoff:
            continue
        categories = [clean_text(child.text or "", max_chars=100) for child in _children(entry, "category")]
        technologies = _resolve_technologies(source, categories)
        if not technologies or not title or not source_url:
            continue
        raw_summary = _text(entry, "summary", "description", "encoded", "content")
        summary = clean_text(raw_summary, max_chars=1200) or title

        for technology in technologies:
            output.append(
                build_item(
                    source,
                    technology=technology,
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    source_url=source_url,
                    published_at=published_at,
                    observed_at=observed_at,
                    categories=categories,
                )
            )
            if len(output) >= max_items:
                return output
    return output
