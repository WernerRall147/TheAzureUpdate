"""GitHub releases and issue announcement parsing."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..models import KnowledgeItem, parse_datetime
from ..text import clean_markdown
from .common import build_item


def _is_recent(value: str | None, observed_at: datetime, since_days: int) -> bool:
    parsed = parse_datetime(value)
    return parsed is None or parsed >= observed_at - timedelta(days=since_days)


def parse_github_releases(
    payload: list[dict[str, Any]],
    source: dict[str, Any],
    *,
    observed_at: datetime,
) -> list[KnowledgeItem]:
    output: list[KnowledgeItem] = []
    since_days = int(source.get("since_days", 21))
    max_items = int(source.get("max_items", 25))
    for release in payload:
        published_at = release.get("published_at") or release.get("created_at")
        if release.get("draft") or not _is_recent(published_at, observed_at, since_days):
            continue
        title = str(release.get("name") or release.get("tag_name") or "").strip()
        url = str(release.get("html_url") or "")
        if not title or not url:
            continue
        categories = ["pre-release"] if release.get("prerelease") else ["release"]
        summary = clean_markdown(str(release.get("body") or title), max_chars=1200)
        output.append(
            build_item(
                source,
                technology=str(source["technology"]),
                external_id=str(release.get("id") or release.get("tag_name") or url),
                title=title,
                summary=summary,
                source_url=url,
                published_at=published_at,
                observed_at=observed_at,
                categories=categories,
            )
        )
        if len(output) >= max_items:
            break
    return output


def parse_github_issues(
    payload: list[dict[str, Any]],
    source: dict[str, Any],
    *,
    observed_at: datetime,
) -> list[KnowledgeItem]:
    output: list[KnowledgeItem] = []
    since_days = int(source.get("since_days", 21))
    max_items = int(source.get("max_items", 25))
    for issue in payload:
        if "pull_request" in issue or not _is_recent(issue.get("created_at"), observed_at, since_days):
            continue
        title = str(issue.get("title") or "").strip()
        url = str(issue.get("html_url") or "")
        if not title or not url:
            continue
        labels = [str(label.get("name", "")) for label in issue.get("labels", []) if isinstance(label, dict)]
        summary = clean_markdown(str(issue.get("body") or title), max_chars=1200)
        output.append(
            build_item(
                source,
                technology=str(source["technology"]),
                external_id=str(issue.get("id") or issue.get("number") or url),
                title=title,
                summary=summary,
                source_url=url,
                published_at=issue.get("created_at"),
                observed_at=observed_at,
                categories=labels,
            )
        )
        if len(output) >= max_items:
            break
    return output
