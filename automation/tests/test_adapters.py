from datetime import UTC, datetime

from knowledge_workflow.adapters import (
    parse_feed,
    parse_github_issues,
    parse_github_releases,
    parse_statuspage_summary,
)


OBSERVED = datetime(2026, 7, 21, 5, 17, tzinfo=UTC)


def source(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "test-source",
        "name": "Test source",
        "source_tier": 1,
        "publisher": "Microsoft",
        "technology": "aks",
        "content_type": "update",
        "max_items": 10,
        "since_days": 30,
    }
    value.update(overrides)
    return value


def test_rss_category_map_emits_one_item_per_matching_technology() -> None:
    payload = """<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <guid>567787</guid>
      <title>[Launched] Generally Available: Encryption in Transit</title>
      <link>https://azure.microsoft.com/updates?id=567787</link>
      <category>Azure Kubernetes Service (AKS)</category>
      <category>Azure Files</category>
      <description>Encryption in transit is now generally available.</description>
      <pubDate>Mon, 20 Jul 2026 14:54:09 +0000</pubDate>
    </item></channel></rss>"""

    items = parse_feed(
        payload,
        source(
            technology=None,
            category_map={"Azure Kubernetes Service (AKS)": "aks"},
        ),
        observed_at=OBSERVED,
    )

    assert len(items) == 1
    assert items[0].technology == "aks"
    assert items[0].lifecycle == "ga"
    assert items[0].external_id == "567787"


def test_atom_feed_is_supported_and_active_content_is_removed() -> None:
    payload = """<feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>App Service platform update</title>
        <link href="https://azure.github.io/AppService/update.html" rel="alternate" />
        <id>app-service-update</id>
        <published>2026-07-20T00:00:00+00:00</published>
        <summary type="html"><![CDATA[<p>Useful text.</p><script>ignore me</script>]]></summary>
      </entry>
    </feed>"""

    items = parse_feed(payload, source(technology="app-service"), observed_at=OBSERVED)

    assert items[0].summary == "Useful text."


def test_github_releases_ignore_drafts_and_mark_prereleases() -> None:
    payload = [
        {
            "id": 1,
            "name": "v2.0.0-preview.1",
            "tag_name": "v2.0.0-preview.1",
            "html_url": "https://github.com/microsoft/qdk/releases/tag/v2.0.0-preview.1",
            "body": "Preview release with **new APIs**.",
            "published_at": "2026-07-20T12:00:00Z",
            "draft": False,
            "prerelease": True,
        },
        {
            "id": 2,
            "name": "draft",
            "html_url": "https://github.com/example/draft",
            "draft": True,
        },
    ]

    items = parse_github_releases(payload, source(technology="quantum"), observed_at=OBSERVED)

    assert len(items) == 1
    assert items[0].lifecycle == "public-preview"
    assert "new APIs" in items[0].summary


def test_github_issues_ignore_pull_requests() -> None:
    payload = [
        {
            "id": 10,
            "number": 7,
            "title": "Python runtime retirement announcement",
            "html_url": "https://github.com/Azure/app-service-announcements/issues/7",
            "body": "Runtime retirement requires customer migration.",
            "created_at": "2026-07-20T12:00:00Z",
            "labels": [{"name": "web-apps"}],
        },
        {
            "id": 11,
            "title": "Not an announcement",
            "pull_request": {"url": "https://api.github.com/pulls/11"},
            "created_at": "2026-07-20T12:00:00Z",
        },
    ]

    items = parse_github_issues(payload, source(technology="app-service"), observed_at=OBSERVED)

    assert len(items) == 1
    assert items[0].content_type == "retirement"
    assert items[0].customer_impact == "high"


def test_statuspage_emits_only_degraded_status() -> None:
    operational = {
        "page": {"url": "https://www.githubstatus.com/"},
        "status": {"indicator": "none", "description": "All Systems Operational"},
        "components": [],
    }
    degraded = {
        "page": {"url": "https://www.githubstatus.com/"},
        "status": {"indicator": "minor", "description": "Minor Service Outage"},
        "components": [{"name": "Actions", "status": "degraded_performance"}],
    }

    assert parse_statuspage_summary(operational, source(technology="github"), observed_at=OBSERVED) == []
    items = parse_statuspage_summary(degraded, source(technology="github"), observed_at=OBSERVED)
    assert items[0].change_type == "incident"
    assert "Actions" in items[0].summary