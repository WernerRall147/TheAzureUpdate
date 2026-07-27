from pathlib import Path

from knowledge_workflow.config import load_registry, load_taxonomy


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]


def test_repository_registry_covers_all_focus_technologies() -> None:
    taxonomy = load_taxonomy(AUTOMATION_ROOT / "config" / "taxonomy.yml")
    registry = load_registry(AUTOMATION_ROOT / "config" / "sources.yml", taxonomy)

    covered = {
        str(source["technology"])
        for source in registry.sources
        if source.get("technology")
    }
    for source in registry.sources:
        covered.update(source.get("category_map", {}).values())

    assert set(taxonomy).difference({"cross-cutting"}).issubset(covered)
    assert len({source["id"] for source in registry.sources}) == len(registry.sources)
