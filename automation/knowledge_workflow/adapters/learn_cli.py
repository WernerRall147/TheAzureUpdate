"""Microsoft Learn CLI adapter for canonical documentation snapshots."""

from __future__ import annotations

import re
import os
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import KnowledgeItem
from ..text import clean_markdown, stable_item_id


LearnRunner = Callable[[str, int], str]


def build_learn_command(
    url: str,
    max_chars: int,
    *,
    platform: str | None = None,
    npx_path: str | None = None,
    node_path: str | None = None,
) -> list[str]:
    platform = platform or os.name
    npx_path = npx_path or shutil.which("npx.cmd" if platform == "nt" else "npx")
    if not npx_path:
        raise FileNotFoundError("npx was not found; install Node.js 22 or newer")
    arguments = [
        npx_path,
        "--yes",
        "@microsoft/learn-cli@0.1.0",
        "fetch",
        url,
        "--max-chars",
        str(max_chars),
    ]
    if platform != "nt":
        return arguments

    node_path = node_path or shutil.which("node.exe")
    npx_cli = Path(npx_path).parent / "node_modules" / "npm" / "bin" / "npx-cli.js"
    if not node_path or not npx_cli.exists():
        raise FileNotFoundError("node.exe or npm's npx-cli.js was not found")
    return [node_path, str(npx_cli), *arguments[1:]]


def run_learn_fetch(url: str, max_chars: int = 12000) -> str:
    command = build_learn_command(url, max_chars)
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "no command output").strip()
        raise RuntimeError(f"Microsoft Learn CLI failed: {detail}") from error
    return completed.stdout


def parse_learn_document(
    markdown: str,
    source: dict[str, Any],
    *,
    observed_at: datetime,
) -> list[KnowledgeItem]:
    title_match = re.search(r"(?m)^#\s+(.+?)\s*$", markdown)
    title = title_match.group(1).strip() if title_match else str(source["name"])
    summary_source = markdown[title_match.end() :] if title_match else markdown
    summary = clean_markdown(summary_source, max_chars=1200) or title
    source_url = str(source["url"])
    technology = str(source["technology"])
    return [
        KnowledgeItem(
            id=stable_item_id(str(source["id"]), source_url, technology),
            external_id=source_url,
            title=title,
            technology=technology,
            content_type="docs",
            change_type="updated",
            lifecycle="unknown",
            source_name=str(source["name"]),
            source_url=source_url,
            source_tier=int(source["source_tier"]),
            publisher=str(source.get("publisher", "Microsoft")),
            summary=summary,
            observed_at=observed_at,
            customer_impact="low",
            csa_outcomes=["skilling"],
            waf_pillars=["operational-excellence"],
            raw_categories=["documentation"],
            why_it_matters=(
                "Canonical documentation is durable evidence for technical readiness and "
                "customer guidance."
            ),
            recommended_action=(
                "Review substantive page changes and update human-authored guidance when needed."
            ),
        )
    ]


def collect_learn_document(
    source: dict[str, Any],
    *,
    observed_at: datetime,
    runner: LearnRunner = run_learn_fetch,
) -> list[KnowledgeItem]:
    markdown = runner(str(source["url"]), int(source.get("max_chars", 12000)))
    return parse_learn_document(markdown, source, observed_at=observed_at)
