"""Compatibility entry point for the collection workflow."""

from __future__ import annotations

import sys

from knowledge_workflow.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["refresh", *sys.argv[1:]]))
