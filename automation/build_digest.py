"""Compatibility entry point for regenerating Markdown views."""

from __future__ import annotations

import sys

from knowledge_workflow.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["rebuild", *sys.argv[1:]]))
