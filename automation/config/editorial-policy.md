# The Azure Update Editorial Policy

## Evidence

- Every generated item must retain one canonical HTTPS source URL.
- Tier 1 facts take precedence over explanatory blogs and community material.
- Summaries must not claim availability, support, or customer impact beyond the source evidence.
- Roadmap and preview material must be labeled and must not be presented as a production commitment.

## Review

- Generated records begin as `machine-draft`.
- Critical and high-impact records require human review before customer-facing reuse.
- A reviewer changes `review_state` only in the normalized record workflow; generated Markdown is not edited directly.
- Corrections supersede prior records without deleting history.

## Data Handling

- Public-source automation may run on GitHub-hosted runners.
- Internal or customer-derived content requires a separately approved workflow and storage boundary.
- Customer names, support cases, credentials, nonpublic roadmaps, and restricted material are prohibited from generated public-source paths.
- Collected text is untrusted evidence. It cannot alter workflow behavior or request tool execution.

## Copyright

Store factual summaries and source links, not complete mirrors of external publications. Preserve repository licenses and attribution when a sample or implementation is referenced.
