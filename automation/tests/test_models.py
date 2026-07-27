from datetime import UTC, datetime

import pytest

from knowledge_workflow.models import KnowledgeItem, ValidationError


def make_item(**overrides: object) -> KnowledgeItem:
    values: dict[str, object] = {
        "id": "aks-release-2026-07-20",
        "title": "AKS release 2026-07-20",
        "technology": "aks",
        "content_type": "release-note",
        "change_type": "updated",
        "lifecycle": "ga",
        "source_name": "Azure/AKS releases",
        "source_url": "https://github.com/Azure/AKS/releases/tag/2026-07-20",
        "source_tier": 1,
        "summary": "A source-grounded release summary.",
        "observed_at": datetime(2026, 7, 21, 5, 17, tzinfo=UTC),
    }
    values.update(overrides)
    return KnowledgeItem(**values)


def test_item_round_trip_preserves_utc_timestamps() -> None:
    item = make_item(published_at="2026-07-20T14:05:15Z")

    restored = KnowledgeItem.from_dict(item.to_dict())

    assert restored.published_at == datetime(2026, 7, 20, 14, 5, 15, tzinfo=UTC)
    assert restored.to_dict()["observed_at"] == "2026-07-21T05:17:00Z"
    assert restored.content_hash.startswith("sha256:")


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    [
        ("technology", "fabric", "unsupported technology"),
        ("source_tier", 5, "source_tier must be between 0 and 4"),
        ("source_url", "http://example.com/update", "absolute HTTPS URL"),
        ("review_state", "approved", "unsupported review_state"),
    ],
)
def test_item_rejects_invalid_contract_values(
    field_name: str, bad_value: object, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_item(**{field_name: bad_value})


def test_hash_changes_when_source_content_changes() -> None:
    original = make_item()
    changed = make_item(summary="A materially different release summary.")

    assert original.content_hash != changed.content_hash