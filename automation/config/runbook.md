# Knowledge Workflow Runbook

## Normal Operation

The scheduled workflow runs daily at 05:17 Africa/Johannesburg. It validates the code, checks Microsoft Learn CLI connectivity, refreshes enabled sources, generates the website post and manifest, and creates or updates one pull request from `automation/daily-azure-update`.

## Manual Recovery

From the repository root:

```powershell
& "automation/.venv/Scripts/python.exe" -m knowledge_workflow.cli refresh --root "."
& "automation/.venv/Scripts/python.exe" -m knowledge_workflow.cli validate --root "."
npm run posts
```

Use `--full-refresh` to ignore stored ETags and `--rebuild-views` to regenerate Markdown from the normalized store.

## Source Failure

1. Open `reports/alerts/source-health.md` and identify the adapter and error.
2. Confirm the URL or repository in `config/sources.yml`.
3. Run only that source with `--source <source-id> --verbose`.
4. Update the adapter fixture before changing parser behavior.
5. Preserve `state/items.json`; a failed source retains its last known good content.

## Duplicate or Incorrect Item

1. Correct deterministic classification or source mapping in automation code or YAML.
2. Add a regression test.
3. Run `refresh --rebuild-views`.
4. Do not edit generated evidence or daily post Markdown directly; change the source, classifier, or renderer.

## GitHub Workflow Prerequisites

- GitHub Actions must be enabled.
- Repository settings must allow GitHub Actions to create pull requests.
- The default branch should require review before merge.
- No Azure credentials are required for Phase 1.

## Future Azure Access

When personalized Service Health is implemented, use GitHub OIDC with a federated identity restricted to this repository and workflow. Grant read-only Resource Graph and Service Health access at the narrowest approved scope. Do not add a client secret.
