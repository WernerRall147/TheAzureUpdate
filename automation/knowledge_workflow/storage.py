"""Atomic JSON persistence for normalized items, manifests, and source health."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import KnowledgeItem


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")
    temporary.replace(path)


def load_items(path: Path) -> dict[str, KnowledgeItem]:
    payload = load_json(path, {"items": []})
    return {item.id: item for item in (KnowledgeItem.from_dict(entry) for entry in payload["items"])}


def write_items(path: Path, items: dict[str, KnowledgeItem]) -> None:
    ordered = sorted(items.values(), key=lambda item: (item.technology, item.id))
    write_json(path, {"version": 1, "items": [item.to_dict() for item in ordered]})
