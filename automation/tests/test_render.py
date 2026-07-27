"""Unit tests for daily post ranking and formatting."""

from datetime import UTC, datetime

from knowledge_workflow.models import KnowledgeItem
from knowledge_workflow.render import (
    _clean_summary,
    _display_title,
    _is_resolved_incident,
    _post_title,
    _relevance_score,
    _render_website_post,
)


OBSERVED = datetime(2026, 7, 21, 5, 17, tzinfo=UTC)


def make_item(**overrides) -> KnowledgeItem:
    payload = {
        "id": "item-1",
        "title": "A capability",
        "technology": "aks",
        "content_type": "update",
        "change_type": "new",
        "lifecycle": "ga",
        "source_name": "Example",
        "source_url": "https://example.com/one",
        "source_tier": 1,
        "summary": "A capability is now available.",
        "observed_at": OBSERVED,
        "customer_impact": "medium",
        "why_it_matters": "It matters.",
        "recommended_action": "Do the thing.",
    }
    payload.update(overrides)
    return KnowledgeItem(**payload)


def test_display_title_drops_redundant_prefixes():
    item = make_item(title="[Launched] Generally Available: Encryption in Transit")
    assert _display_title(item) == "Encryption in Transit"


def test_display_title_keeps_plain_titles():
    item = make_item(title="Repository admins can archive pull requests")
    assert _display_title(item) == "Repository admins can archive pull requests"


def test_clean_summary_trims_publisher_ellipsis():
    assert _clean_summary("A thing happened\u2026") == "A thing happened..."


def test_clean_summary_caps_long_status_timelines():
    long_text = ("Resolved - this incident has been resolved. " * 20).strip()
    result = _clean_summary(long_text)
    assert len(result) <= 320


def test_resolved_incident_is_downranked_below_a_launch():
    incident = make_item(
        id="incident",
        change_type="incident",
        lifecycle="unknown",
        customer_impact="medium",
        summary="Jul 20 Resolved - this incident has been resolved.",
    )
    launch = make_item(id="launch", change_type="new", lifecycle="ga")
    assert _is_resolved_incident(incident)
    assert _relevance_score(launch) > _relevance_score(incident)


def test_breaking_change_outranks_a_launch():
    breaking = make_item(id="breaking", change_type="breaking-change", customer_impact="critical")
    launch = make_item(id="launch", change_type="new", lifecycle="ga")
    assert _relevance_score(breaking) > _relevance_score(launch)


def test_post_title_leads_with_date_and_lead_story():
    lead = make_item(title="[Launched] Generally Available: Encryption in Transit")
    assert _post_title(OBSERVED, lead, 5) == "21 July 2026: Encryption in Transit, and 4 more"


def test_post_title_without_items():
    assert _post_title(OBSERVED, None, 0) == "Azure Update - 21 July 2026"


def test_resolved_incident_is_not_action_required():
    incident = make_item(
        id="incident",
        change_type="incident",
        customer_impact="high",
        summary="Resolved - this incident has been resolved.",
    )
    post = _render_website_post(OBSERVED, [incident], {})
    assert "## Action required" not in post


def test_post_is_featured_only_for_high_impact():
    low = make_item(customer_impact="low", change_type="updated", lifecycle="unknown")
    assert "featured: false" in _render_website_post(OBSERVED, [low], {})

    high = make_item(customer_impact="critical", change_type="breaking-change")
    assert "featured: true" in _render_website_post(OBSERVED, [high], {})


def test_launch_items_omit_boilerplate_guidance():
    # Two launches: the highest ranked becomes the lead story and the other
    # falls into "New and notable".
    launches = [
        make_item(id=f"launch-{n}", change_type="new", lifecycle="ga", customer_impact="medium")
        for n in range(2)
    ]
    post = _render_website_post(OBSERVED, launches, {})
    # Guidance is reserved for action-required items so launches do not repeat
    # the same two sentences for every entry.
    assert post.count("**Next action:**") == 0
    assert "## New and notable" in post


def test_action_items_keep_guidance_and_smaller_items_collapse():
    action = make_item(id="sec", change_type="security", customer_impact="high")
    minor = [
        make_item(id=f"minor-{n}", change_type="updated", lifecycle="unknown", customer_impact="low")
        for n in range(3)
    ]
    post = _render_website_post(OBSERVED, [action, *minor], {})
    assert "**Next action:**" in post
    assert "<details>" in post
    assert "3 smaller updates" in post


def test_table_cells_escape_pipes():
    item = make_item(title="Alpha | Beta")
    post = _render_website_post(OBSERVED, [item], {})
    assert "Alpha \\| Beta" in post


def test_source_health_reports_failures():
    item = make_item()
    post = _render_website_post(
        OBSERVED, [item], {"src": {"status": "error", "name": "Broken feed"}}
    )
    assert "Broken feed" in post
