import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

import httpx

from knowledge_workflow.pipeline import refresh, validate_repository


OBSERVED = datetime(2026, 7, 21, 5, 17, tzinfo=UTC)


def write_fixture_config(root: Path) -> None:
    meta = root / "automation" / "config"
    meta.mkdir(parents=True)
    (root / "automation" / "docs").mkdir()
    (root / "automation" / "README.md").write_text("# Automation\n", encoding="utf-8")
    (root / "automation" / "docs" / "Plan.md").write_text("# Plan\n", encoding="utf-8")
    taxonomy = Path(__file__).resolve().parents[1] / "config" / "taxonomy.yml"
    (meta / "taxonomy.yml").write_text(taxonomy.read_text(encoding="utf-8"), encoding="utf-8")
    (meta / "sources.yml").write_text(
        """version: 1
defaults:
  enabled: true
  timeout_seconds: 3
  max_retries: 0
  max_items: 10
  since_days: 30
allowed_hosts:
  - example.com
  - github.com
allowed_github_owners: []
sources:
  - id: fixture-feed
    name: Fixture feed
    adapter: rss
    url: https://example.com/feed.xml
    source_tier: 1
    publisher: Microsoft
    technology: aks
    content_type: update
""",
        encoding="utf-8",
    )


def test_refresh_renders_and_then_detects_no_substantive_change(tmp_path: Path) -> None:
    root = tmp_path / "TheAzureUpdate"
    write_fixture_config(root)
    feed = b"""<rss version="2.0"><channel><item>
      <guid>one</guid><title>Generally Available: Test capability</title>
      <link>https://github.com/example/update</link>
      <description>A useful capability is generally available.</description>
      <pubDate>Mon, 20 Jul 2026 14:54:09 +0000</pubDate>
    </item></channel></rss>"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=feed, headers={"etag": '"one"'})

    first = refresh(root, observed_at=OBSERVED, transport=httpx.MockTransport(handler))
    second = refresh(root, observed_at=OBSERVED, transport=httpx.MockTransport(handler))
    rebuilt = refresh(
      root,
      observed_at=OBSERVED,
      transport=httpx.MockTransport(handler),
      rebuild_views=True,
    )

    assert first.changed_count == 1
    assert second.changed_count == 0
    assert rebuilt.changed_count == 0
    daily_dir = root / "automation" / "reports" / "daily"
    assert (daily_dir / "latest.md").exists()
    assert (root / "knowledge" / "AKS" / "updates" / "latest.md").exists()
    website_post = root / "src" / "posts" / "azure-update-2026-07-21" / "index.md"
    assert website_post.exists()
    post_text = website_post.read_text(encoding="utf-8")
    assert post_text.startswith("---\nid: azure-update-2026-07-21")
    # The title leads with the date and the highest-ranked item, and the
    # redundant "Generally Available:" prefix is dropped because the
    # lifecycle is shown beside the item.
    assert 'title: "21 July 2026: Test capability"' in post_text
    assert "## At a glance" in post_text
    assert "## The one to read first" in post_text
    assert "[Test capability](https://github.com/example/update)" in post_text
    assert validate_repository(root) == []
    payload = json.loads((root / "automation" / "state" / "items.json").read_text(encoding="utf-8"))
    assert len(payload["items"]) == 1

    digest = (daily_dir / "latest.md").read_text(encoding="utf-8")
    generated_link = re.search(r"\]\((\.\./[^)]+\.md)\)", digest)
    assert generated_link is not None
    target = (daily_dir / unquote(generated_link.group(1))).resolve()
    assert target.exists()

    hub = root / "automation" / "Hub.md"
    hub.write_text(hub.read_text(encoding="utf-8") + "\n[Broken](missing.md)\n", encoding="utf-8")
    assert any("broken local link: missing.md" in error for error in validate_repository(root))