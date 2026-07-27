"""Command-line interface for refreshing and validating the knowledge hub."""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from .config import load_registry, load_taxonomy
from .layout import RepositoryLayout
from .pipeline import rebuild_views, refresh, validate_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="technology-knowledge")
    subcommands = parser.add_subparsers(dest="command", required=True)

    refresh_parser = subcommands.add_parser("refresh", help="Collect, merge, and render knowledge")
    refresh_parser.add_argument("--verbose", action="store_true")
    refresh_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    refresh_parser.add_argument("--full-refresh", action="store_true")
    refresh_parser.add_argument(
        "--rebuild-views",
        action="store_true",
        help="Regenerate all Markdown views from the normalized item store",
    )
    refresh_parser.add_argument("--source", action="append", dest="sources")
    refresh_parser.add_argument("--as-of", help="UTC ISO timestamp for deterministic runs")

    validate_parser = subcommands.add_parser("validate", help="Validate generated content and provenance")
    validate_parser.add_argument("--verbose", action="store_true")
    validate_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])

    rebuild_parser = subcommands.add_parser("rebuild", help="Regenerate views from normalized data")
    rebuild_parser.add_argument("--verbose", action="store_true")
    rebuild_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    rebuild_parser.add_argument("--as-of", help="UTC ISO timestamp for deterministic runs")

    list_parser = subcommands.add_parser("list-sources", help="List configured source adapters")
    list_parser.add_argument("--verbose", action="store_true")
    list_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.command == "refresh":
        observed_at = (
            datetime.fromisoformat(args.as_of.replace("Z", "+00:00")).astimezone(UTC)
            if args.as_of
            else None
        )
        result = refresh(
            args.root.resolve(),
            observed_at=observed_at,
            full_refresh=args.full_refresh,
            rebuild_views=args.rebuild_views,
            selected_sources=set(args.sources) if args.sources else None,
        )
        print(
            f"Collected {result.collected_count} items; "
            f"{result.changed_count} substantive changes; "
            f"{len(result.failed_sources)} source failures."
        )
        return 0

    if args.command == "validate":
        errors = validate_repository(args.root.resolve())
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("Knowledge repository validation passed.")
        return 0

    if args.command == "rebuild":
        observed_at = (
            datetime.fromisoformat(args.as_of.replace("Z", "+00:00")).astimezone(UTC)
            if args.as_of
            else None
        )
        count = rebuild_views(args.root.resolve(), observed_at=observed_at)
        print(f"Rebuilt Markdown views for {count} normalized items.")
        return 0

    layout = RepositoryLayout(args.root)
    taxonomy = load_taxonomy(layout.config_dir / "taxonomy.yml")
    registry = load_registry(layout.config_dir / "sources.yml", taxonomy)
    for source in registry.sources:
        print(f"{source['id']}: {source['adapter']} - {source['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
