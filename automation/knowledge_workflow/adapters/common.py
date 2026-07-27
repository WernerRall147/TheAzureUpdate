"""Shared adapter construction helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..classify import (
    action_text,
    csa_metadata,
    infer_change_type,
    infer_content_type,
    infer_customer_impact,
    infer_lifecycle,
)
from ..models import KnowledgeItem
from ..text import stable_item_id


def build_item(
    source: dict[str, Any],
    *,
    technology: str,
    external_id: str,
    title: str,
    summary: str,
    source_url: str,
    published_at: datetime | str | None,
    observed_at: datetime,
    categories: list[str] | None = None,
) -> KnowledgeItem:
    categories = categories or []
    lifecycle = infer_lifecycle(title, summary, categories)
    change_type = infer_change_type(title, summary, categories)
    content_type = infer_content_type(str(source.get("content_type", "update")), change_type)
    customer_impact = infer_customer_impact(change_type, lifecycle, summary)
    outcomes, pillars = csa_metadata(technology, change_type, lifecycle)
    why_it_matters, recommended_action = action_text(change_type, lifecycle)

    return KnowledgeItem(
        id=stable_item_id(str(source["id"]), external_id, technology),
        external_id=external_id,
        title=title,
        technology=technology,
        content_type=content_type,
        change_type=change_type,
        lifecycle=lifecycle,
        source_name=str(source["name"]),
        source_url=source_url,
        source_tier=int(source["source_tier"]),
        publisher=str(source.get("publisher", "Microsoft")),
        summary=summary,
        published_at=published_at,
        observed_at=observed_at,
        customer_impact=customer_impact,
        csa_outcomes=outcomes,
        waf_pillars=pillars,
        raw_categories=categories,
        why_it_matters=why_it_matters,
        recommended_action=recommended_action,
    )
