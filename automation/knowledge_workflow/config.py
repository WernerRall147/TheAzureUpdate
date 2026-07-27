"""Load and validate declarative source and technology configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from .models import TECHNOLOGIES, ValidationError


SUPPORTED_ADAPTERS = {
    "rss",
    "statuspage",
    "github-releases",
    "github-issues",
    "learn-cli",
}


@dataclass(slots=True, frozen=True)
class Registry:
    defaults: dict[str, Any]
    allowed_hosts: frozenset[str]
    allowed_github_owners: frozenset[str]
    sources: tuple[dict[str, Any], ...]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValidationError(f"{path} must contain a YAML mapping")
    return data


def load_taxonomy(path: Path) -> dict[str, dict[str, str]]:
    data = load_yaml(path)
    technologies = data.get("technologies")
    if not isinstance(technologies, dict):
        raise ValidationError("taxonomy.yml must define technologies")

    missing = TECHNOLOGIES.difference(technologies)
    if missing:
        raise ValidationError(f"taxonomy is missing technologies: {sorted(missing)}")

    for slug, config in technologies.items():
        if not isinstance(config, dict) or not config.get("display_name") or not config.get("folder"):
            raise ValidationError(f"technology {slug} must define display_name and folder")
    return technologies


def load_registry(path: Path, taxonomy: dict[str, dict[str, str]]) -> Registry:
    data = load_yaml(path)
    defaults = data.get("defaults", {})
    allowed_hosts = frozenset(str(host).casefold() for host in data.get("allowed_hosts", []))
    allowed_github_owners = frozenset(
        str(owner).casefold() for owner in data.get("allowed_github_owners", [])
    )
    raw_sources = data.get("sources")
    if not isinstance(raw_sources, list):
        raise ValidationError("sources.yml must define a sources list")

    seen_ids: set[str] = set()
    sources: list[dict[str, Any]] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, dict):
            raise ValidationError("every source entry must be a mapping")
        source = {**defaults, **raw_source}
        source_id = str(source.get("id", "")).strip()
        adapter = str(source.get("adapter", "")).strip()
        if not source_id or source_id in seen_ids:
            raise ValidationError(f"source id is missing or duplicated: {source_id!r}")
        if adapter not in SUPPORTED_ADAPTERS:
            raise ValidationError(f"source {source_id} uses unsupported adapter {adapter!r}")
        seen_ids.add(source_id)

        technology = source.get("technology")
        if technology and technology not in taxonomy:
            raise ValidationError(f"source {source_id} has unknown technology {technology!r}")
        category_map = source.get("category_map", {})
        for mapped_technology in category_map.values():
            if mapped_technology not in taxonomy:
                raise ValidationError(
                    f"source {source_id} maps to unknown technology {mapped_technology!r}"
                )

        url = source.get("url")
        if url:
            host = (urlparse(str(url)).hostname or "").casefold()
            if host not in allowed_hosts:
                raise ValidationError(f"source {source_id} host is not allowlisted: {host}")
        repository = source.get("repository")
        if repository:
            owner, separator, _ = str(repository).partition("/")
            if not separator or owner.casefold() not in allowed_github_owners:
                raise ValidationError(
                    f"source {source_id} GitHub owner is not allowlisted: {owner!r}"
                )
        sources.append(source)

    return Registry(
        defaults=dict(defaults),
        allowed_hosts=allowed_hosts,
        allowed_github_owners=allowed_github_owners,
        sources=tuple(sources),
    )
