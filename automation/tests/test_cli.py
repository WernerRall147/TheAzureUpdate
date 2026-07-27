from knowledge_workflow.cli import _parser


def test_verbose_is_supported_after_subcommand() -> None:
    args = _parser().parse_args(["refresh", "--verbose", "--source", "azure-updates"])

    assert args.command == "refresh"
    assert args.verbose is True
    assert args.sources == ["azure-updates"]