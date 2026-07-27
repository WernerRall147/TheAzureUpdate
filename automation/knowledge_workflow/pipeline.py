"""End-to-end collection, merge, validation, and render orchestration."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from .adapters import parse_feed, parse_github_issues, parse_github_releases, parse_statuspage_summary
from .adapters.learn_cli import LearnRunner, collect_learn_document, run_learn_fetch
from .config import Registry, load_registry, load_taxonomy
from .http_client import FetchError, SafeHttpClient, json_payload
from .layout import RepositoryLayout
from .models import KnowledgeItem, isoformat
from .render import GENERATED_MARKER, render_all
from .storage import load_items, load_json, write_items, write_json


LOGGER = logging.getLogger(__name__)
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)")


@dataclass(slots=True, frozen=True)
class RefreshResult:
    collected_count: int
    changed_count: int
    failed_sources: tuple[str, ...]
    changed_ids: frozenset[str]


def _github_url(source: dict[str, Any]) -> str:
    repository = str(source["repository"])
    max_items = int(source.get("max_items", 25))
    if source["adapter"] == "github-releases":
        return f"https://api.github.com/repos/{repository}/releases?per_page={max_items}"
    labels = ",".join(str(label) for label in source.get("labels", []))
    return (
        f"https://api.github.com/repos/{repository}/issues?state=all&sort=created&direction=desc"
        f"&per_page={max_items}&labels={quote(labels)}"
    )


def _collect_http_source(
    client: SafeHttpClient,
    source: dict[str, Any],
    state: dict[str, Any],
    *,
    observed_at: datetime,
    full_refresh: bool,
) -> tuple[list[KnowledgeItem], dict[str, Any], bool]:
    adapter = str(source["adapter"])
    url = str(source.get("url") or _github_url(source))
    response = client.get(
        url,
        etag=None if full_refresh else state.get("etag"),
        last_modified=None if full_refresh else state.get("last_modified"),
        headers={"X-GitHub-Api-Version": "2022-11-28"} if adapter.startswith("github-") else None,
    )
    new_state = dict(state)
    new_state.update(
        {
            "name": source["name"],
            "status": "healthy",
            "error": None,
            "etag": response.etag or state.get("etag"),
            "last_modified": response.last_modified or state.get("last_modified"),
        }
    )
    if response.not_modified:
        return [], new_state, False

    if adapter == "rss":
        items = parse_feed(response.content, source, observed_at=observed_at)
    elif adapter == "statuspage":
        items = parse_statuspage_summary(json_payload(response), source, observed_at=observed_at)
    elif adapter == "github-releases":
        items = parse_github_releases(json_payload(response), source, observed_at=observed_at)
    elif adapter == "github-issues":
        items = parse_github_issues(json_payload(response), source, observed_at=observed_at)
    else:
        raise FetchError(f"unsupported HTTP adapter: {adapter}")
    new_state["item_count"] = len(items)
    return items, new_state, True


def _merge_source_items(
    existing: dict[str, KnowledgeItem],
    collected: list[KnowledgeItem],
    source: dict[str, Any],
    *,
    fetched: bool,
) -> tuple[dict[str, KnowledgeItem], set[str]]:
    merged = dict(existing)
    changed: set[str] = set()
    source_name = str(source["name"])
    incoming_ids = {item.id for item in collected}

    if fetched and source.get("replace_on_fetch"):
        for item_id, existing_item in list(merged.items()):
            if existing_item.source_name == source_name and item_id not in incoming_ids:
                del merged[item_id]
                changed.add(item_id)

    for item in collected:
        previous = merged.get(item.id)
        if previous and previous.content_hash == item.content_hash:
            continue
        merged[item.id] = item
        changed.add(item.id)
    return merged, changed


def _validate_generated_links(root: Path) -> list[str]:
    errors: list[str] = []
    resolved_root = root.resolve()
    for path in root.rglob("*.md"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if GENERATED_MARKER not in content[:500]:
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(content):
            href = match.group(1).strip("<>")
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(resolved_root):
                errors.append(f"{path.relative_to(root)}: local link escapes Technology root: {href}")
            elif not target.exists():
                errors.append(f"{path.relative_to(root)}: broken local link: {href}")
    return errors


def refresh(
    root: Path,
    *,
    registry_path: Path | None = None,
    taxonomy_path: Path | None = None,
    observed_at: datetime | None = None,
    full_refresh: bool = False,
    rebuild_views: bool = False,
    selected_sources: set[str] | None = None,
    transport: Any = None,
    learn_runner: LearnRunner = run_learn_fetch,
) -> RefreshResult:
    observed_at = observed_at or datetime.now(UTC).replace(microsecond=0)
    layout = RepositoryLayout(root)
    registry_path = registry_path or layout.config_dir / "sources.yml"
    taxonomy_path = taxonomy_path or layout.config_dir / "taxonomy.yml"
    taxonomy = load_taxonomy(taxonomy_path)
    registry: Registry = load_registry(registry_path, taxonomy)
    items_path = layout.state_dir / "items.json"
    freshness_path = layout.state_dir / "freshness.json"
    items = load_items(items_path)
    source_health: dict[str, Any] = load_json(freshness_path, {"version": 1, "sources": {}}).get("sources", {})
    changed_ids: set[str] = set()
    failed_sources: list[str] = []
    collected_count = 0
    enabled_sources = [
        source
        for source in registry.sources
        if source.get("enabled", True)
        and (selected_sources is None or str(source["id"]) in selected_sources)
    ]

    with SafeHttpClient(
        allowed_hosts=registry.allowed_hosts,
        timeout_seconds=float(registry.defaults.get("timeout_seconds", 30)),
        max_retries=int(registry.defaults.get("max_retries", 3)),
        token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"),
        transport=transport,
        sleeper=(lambda _: None) if transport is not None else __import__("time").sleep,
    ) as client:
        for source in enabled_sources:
            source_id = str(source["id"])
            previous_state = dict(source_health.get(source_id, {}))
            try:
                if source["adapter"] == "learn-cli":
                    collected = collect_learn_document(
                        source,
                        observed_at=observed_at,
                        runner=learn_runner,
                    )
                    new_state = {
                        **previous_state,
                        "name": source["name"],
                        "status": "healthy",
                        "error": None,
                        "item_count": len(collected),
                    }
                    fetched = True
                else:
                    collected, new_state, fetched = _collect_http_source(
                        client,
                        source,
                        previous_state,
                        observed_at=observed_at,
                        full_refresh=full_refresh,
                    )
                collected_count += len(collected)
                items, source_changes = _merge_source_items(items, collected, source, fetched=fetched)
                changed_ids.update(source_changes)
                if source_changes:
                    new_state["last_content_change"] = isoformat(observed_at)
                elif "last_content_change" not in new_state:
                    new_state["last_content_change"] = "none"
                source_health[source_id] = new_state
            except Exception as error:
                LOGGER.exception("Source %s failed", source_id)
                failed_sources.append(source_id)
                error_text = f"{type(error).__name__}: {error}"
                source_health[source_id] = {
                    **previous_state,
                    "name": source["name"],
                    "status": "error",
                    "error": error_text,
                    "last_error_at": isoformat(observed_at),
                }

    if enabled_sources and len(failed_sources) == len(enabled_sources) and not items:
        raise RuntimeError("all enabled sources failed and no last known good content exists")

    state_changed = source_health != load_json(freshness_path, {"version": 1, "sources": {}}).get("sources", {})
    if changed_ids or not items_path.exists():
        write_items(items_path, items)
    if changed_ids or state_changed or not freshness_path.exists():
        write_json(freshness_path, {"version": 1, "sources": source_health})

    render_ids = set(items) if rebuild_views else changed_ids
    if render_ids or not (layout.state_dir / "manifest.json").exists() or state_changed:
        render_all(
            root,
            items=items,
            changed_ids=render_ids,
            source_health=source_health,
            taxonomy=taxonomy,
            sources=registry.sources,
            as_of=observed_at,
        )

    return RefreshResult(
        collected_count=collected_count,
        changed_count=len(changed_ids),
        failed_sources=tuple(failed_sources),
        changed_ids=frozenset(changed_ids),
    )


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    layout = RepositoryLayout(root)
    taxonomy = load_taxonomy(layout.config_dir / "taxonomy.yml")
    registry = load_registry(layout.config_dir / "sources.yml", taxonomy)
    items = load_items(layout.state_dir / "items.json")
    manifest = load_json(layout.state_dir / "manifest.json", {"items": {}}).get("items", {})

    allowed_hosts = registry.allowed_hosts
    for item in items.values():
        try:
            item.validate()
        except Exception as error:
            errors.append(f"{item.id}: {error}")
        host = urlparse(item.source_url).hostname
        if not host or host.casefold() not in allowed_hosts:
            errors.append(f"{item.id}: source URL host is not allowlisted: {host}")
        relative = manifest.get(item.id)
        if not relative or not (root / relative).exists():
            errors.append(f"{item.id}: generated Markdown is missing")
    errors.extend(_validate_generated_links(root))
    return errors


def rebuild_views(root: Path, *, observed_at: datetime | None = None) -> int:
    observed_at = observed_at or datetime.now(UTC).replace(microsecond=0)
    layout = RepositoryLayout(root)
    taxonomy = load_taxonomy(layout.config_dir / "taxonomy.yml")
    registry = load_registry(layout.config_dir / "sources.yml", taxonomy)
    items = load_items(layout.state_dir / "items.json")
    source_health = load_json(
        layout.state_dir / "freshness.json", {"version": 1, "sources": {}}
    ).get("sources", {})
    render_all(
        root,
        items=items,
        changed_ids=set(items),
        source_health=source_health,
        taxonomy=taxonomy,
        sources=registry.sources,
        as_of=observed_at,
    )
    return len(items)
