# Query Guide

Use these patterns with GitHub Copilot in this workspace. Ground website drafts in `automation/state/items.json`, `automation/reports/`, and `knowledge/`, and preserve canonical evidence links.

## Daily Triage

- What changed in the last seven days, grouped by action required and customer opportunity?
- Which current items are critical or high impact?
- Which sources failed or became stale?

## Customer Readiness

- Which retirements in the next 180 days affect this customer's services or versions?
- Separate generally available, preview, roadmap, and live availability evidence.
- Map these changes to Well-Architected pillars and propose verification steps.

## Architecture and Growth

- Which new capabilities remove a known delivery blocker?
- Which changes create an APIM, AKS, App Service, data, GitHub, Quantum, or Foundry expansion discussion?
- What reusable architecture note, workshop, or lab should be updated?

## Required Answer Shape

1. State the answer date and evidence scope.
2. Give the concise conclusion.
3. Link canonical evidence.
4. State lifecycle and regional caveats.
5. Explain customer impact and the next verification action.
6. Identify the review state.
7. Use live tools for volatile health, quota, model, target, provider, and regional availability data.

## Website Draft

- Use `/Generate Daily Azure Update` to run the repository prompt.
- Review `src/posts/azure-update-YYYY-MM-DD/index.md` before publication.
- Keep generated posts factual and concise; never imply preview or roadmap content is GA.
