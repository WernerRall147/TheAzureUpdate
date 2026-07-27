---
name: "Generate Daily Azure Update"
description: "Collect first-party updates and generate today's reviewable The Azure Update blog post"
agent: "agent"
---
Use [the automation runbook](../../automation/README.md) to generate today's source-grounded Azure Update.

1. Refresh public sources with `python -m knowledge_workflow.cli refresh --root .`.
2. Run `npm run posts`, then validate with `python -m knowledge_workflow.cli validate --root .` and `python -m pytest automation`.
3. Review `src/posts/azure-update-YYYY-MM-DD/index.md` for concise wording, canonical links, lifecycle accuracy, and customer impact.
4. Never include internal or confidential material, and never present preview or roadmap content as GA.
5. Report the post path, item count, source failures, and validation results. Do not publish or merge without human review.
