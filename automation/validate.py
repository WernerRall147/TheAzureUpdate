"""Compatibility entry point for repository validation."""

from __future__ import annotations

import sys

from knowledge_workflow.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["validate", *sys.argv[1:]]))
