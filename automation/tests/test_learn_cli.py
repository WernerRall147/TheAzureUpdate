from datetime import UTC, datetime

from knowledge_workflow.adapters.learn_cli import build_learn_command, collect_learn_document


def test_learn_cli_markdown_becomes_a_document_item() -> None:
    source = {
        "id": "aks-docs",
        "name": "AKS docs",
        "adapter": "learn-cli",
        "url": "https://learn.microsoft.com/azure/aks/release-tracker",
        "source_tier": 1,
        "publisher": "Microsoft",
        "technology": "aks",
        "content_type": "docs",
    }

    items = collect_learn_document(
        source,
        observed_at=datetime(2026, 7, 21, tzinfo=UTC),
        runner=lambda _url, _max_chars: "# AKS release tracker\n\nCurrent rollout details.",
    )

    assert items[0].title == "AKS release tracker"
    assert items[0].summary == "Current rollout details."
    assert items[0].content_type == "docs"
    assert items[0].change_type == "updated"
    assert items[0].lifecycle == "unknown"
    assert items[0].customer_impact == "low"


def test_learn_command_uses_node_for_windows_shim(tmp_path) -> None:
    node_modules = tmp_path / "node_modules" / "npm" / "bin"
    node_modules.mkdir(parents=True)
    (node_modules / "npx-cli.js").write_text("", encoding="utf-8")
    command = build_learn_command(
        "https://learn.microsoft.com/azure/aks/release-tracker",
        12000,
        platform="nt",
        npx_path=str(tmp_path / "npx.cmd"),
        node_path=r"C:\Program Files\nodejs\node.exe",
    )

    assert command[0] == r"C:\Program Files\nodejs\node.exe"
    assert command[1].endswith("npx-cli.js")
    assert command[2] == "--yes"


def test_learn_command_executes_npx_directly_on_linux() -> None:
    command = build_learn_command(
        "https://learn.microsoft.com/azure/aks/release-tracker",
        12000,
        platform="posix",
        npx_path="/usr/bin/npx",
    )

    assert command[0] == "/usr/bin/npx"
    assert command[-1] == "12000"
