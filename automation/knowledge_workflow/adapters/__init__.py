"""Source adapters for public, structured technology feeds."""

from .github import parse_github_issues, parse_github_releases
from .rss import parse_feed
from .statuspage import parse_statuspage_summary

__all__ = [
    "parse_feed",
    "parse_github_issues",
    "parse_github_releases",
    "parse_statuspage_summary",
]
