"""Atlassian Statuspage summary parsing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import KnowledgeItem
from .common import build_item


def parse_statuspage_summary(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    observed_at: datetime,
) -> list[KnowledgeItem]:
    status = payload.get("status", {})
    indicator = str(status.get("indicator", "none"))
    description = str(status.get("description", "All Systems Operational"))
    if indicator == "none":
        return []

    page = payload.get("page", {})
    page_url = str(page.get("url") or "https://www.githubstatus.com/")
    components = [
        f"{component.get('name')}: {component.get('status')}"
        for component in payload.get("components", [])
        if component.get("status") != "operational"
    ]
    summary = f"{description}. " + "; ".join(components)
    return [
        build_item(
            source,
            technology=str(source["technology"]),
            external_id=f"{observed_at.date().isoformat()}-{indicator}",
            title=f"GitHub status: {description}",
            summary=summary.strip(),
            source_url=page_url,
            published_at=observed_at,
            observed_at=observed_at,
            categories=["incident", indicator],
        )
    ]
