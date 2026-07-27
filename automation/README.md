# The Azure Update Knowledge Automation

This package collects trusted public sources, preserves normalized evidence, and generates a reviewable daily post for [The Azure Update](https://www.theazureupdate.com/). Evidence stays under `knowledge/`; publishable posts are written to `src/posts/azure-update-YYYY-MM-DD/index.md`.

## Requirements

- Python 3.11 or newer
- Node.js 22 or newer for `@microsoft/learn-cli`
- Network access to the hosts allowlisted in `config/sources.yml`
- No Azure credentials for Phase 1

## Local Setup

From the repository root on Windows:

```powershell
python -m venv "automation/.venv"
& "automation/.venv/Scripts/python.exe" -m pip install --require-hashes -r "automation/requirements.lock"
& "automation/.venv/Scripts/python.exe" -m pip install --no-deps -e "automation"
```

## Validate

```powershell
Push-Location "automation"
python -m pytest
python -m knowledge_workflow.cli validate --root ".."
Pop-Location
```

## Refresh

Run a narrow source while developing:

```powershell
Push-Location "automation"
python -m knowledge_workflow.cli refresh --root ".." --source azure-updates
Pop-Location
```

Run all enabled public sources:

```powershell
Push-Location "automation"
python -m knowledge_workflow.cli refresh --root ".."
python -m knowledge_workflow.cli validate --root ".."
Pop-Location

npm run posts
```

Useful options:

- `--full-refresh`: bypass stored ETag and Last-Modified values.
- `--rebuild-views`: regenerate Markdown from normalized data without deleting state.
- `--source <id>`: run one or more selected sources.
- `--as-of <ISO timestamp>`: make a test or recovery run deterministic.
- `--verbose`: show detailed fetch and adapter logs.

## Architecture

- `config/taxonomy.yml`: technology folder and display-name mapping.
- `config/sources.yml`: enabled sources, adapters, categories, and allowlists.
- `knowledge_workflow/adapters/`: pure parsing functions for RSS/Atom, GitHub, Statuspage, and Learn CLI output.
- `knowledge_workflow/http_client.py`: HTTPS allowlist, redirect validation, conditional requests, and retry handling.
- `knowledge_workflow/pipeline.py`: source orchestration, last-known-good merge, source health, and validation.
- `knowledge_workflow/render.py`: evidence pages, reports, and website post generation.
- `state/items.json`: normalized source-of-truth records.
- `state/manifest.json`: generated item path ownership used for safe cleanup.
- `reports/`: daily digests, alert views, and source health.
- `docs/`: implementation plan, CSA role context, and technology scope.
- `../knowledge/`: generated public evidence grouped by technology.
- `../src/posts/azure-update-*/`: website-ready daily posts.

## Adding a Source

1. Prefer a first-party API, RSS/Atom feed, GitHub API, or Microsoft Learn page.
2. Add its host or GitHub owner only after reviewing ownership and terms.
3. Add the source to `config/sources.yml`.
4. Add or update a parser fixture.
5. Run the source alone.
6. Run the full test and repository validation suite.

Generated files contain a marker and must not be edited directly. Files without the marker remain human-owned.

## Security

- Source URLs and redirects must remain HTTPS and allowlisted.
- Collected HTML is converted to inert text; scripts, forms, styles, iframes, and SVG are ignored.
- Fetched text is data, never workflow instruction.
- Dependencies are hash locked.
- GitHub Actions dependencies are pinned to immutable commit SHAs.
- Internal or confidential content must never enter this public repository or workflow.
- Future Azure access must use OIDC or managed identity with least privilege.
