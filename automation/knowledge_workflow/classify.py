"""Deterministic lifecycle, impact, and CSA relevance classification."""

from __future__ import annotations

from collections.abc import Iterable


def _haystack(title: str, summary: str, categories: Iterable[str]) -> str:
    return " ".join([title, summary, *categories]).casefold()


def infer_lifecycle(title: str, summary: str, categories: Iterable[str]) -> str:
    text = _haystack(title, summary, categories)
    if "retired" in text or "retirement" in text:
        return "retired" if "has retired" in text or "is retired" in text else "deprecated"
    if "private preview" in text:
        return "private-preview"
    if "public preview" in text or "in preview" in text or "pre-release" in text:
        return "public-preview"
    if "in development" in text:
        return "in-development"
    if "generally available" in text or "general availability" in text or "[launched]" in text:
        return "ga"
    return "unknown"


def infer_change_type(title: str, summary: str, categories: Iterable[str]) -> str:
    text = _haystack(title, summary, categories)
    if "retirement" in text or "deprecated" in text or "deprecation" in text:
        return "deprecated"
    if "retired" in text:
        return "retired"
    if "breaking change" in text:
        return "breaking-change"
    if "security" in text or "cve" in text or "vulnerability" in text:
        return "security"
    if "incident" in text or "degraded" in text or "disruption" in text or "outage" in text:
        return "incident"
    if "maintenance" in text:
        return "maintenance"
    if "pricing" in text or "billing" in text or "cost" in text:
        return "pricing"
    if "new region" in text or "region availability" in text:
        return "region-availability"
    if "release" in text or "available" in text or "announcing" in text:
        return "new"
    return "updated"


def infer_content_type(configured: str, change_type: str) -> str:
    if change_type in {"deprecated", "retired"}:
        return "retirement"
    if change_type == "security":
        return "security"
    return configured


def infer_customer_impact(change_type: str, lifecycle: str, summary: str) -> str:
    text = summary.casefold()
    if change_type in {"breaking-change", "retired"}:
        return "critical"
    if change_type in {"deprecated", "security"}:
        return "high"
    if change_type == "incident" and "resolved" not in text:
        return "high"
    if change_type in {"incident", "maintenance", "pricing", "region-availability"}:
        return "medium"
    if lifecycle in {"ga", "public-preview", "private-preview"}:
        return "medium"
    return "low"


def csa_metadata(technology: str, change_type: str, lifecycle: str) -> tuple[list[str], list[str]]:
    outcomes = {"skilling"}
    pillars = {"operational-excellence"}

    if change_type in {"deprecated", "retired", "breaking-change", "incident", "maintenance"}:
        outcomes.add("blocker-mitigation")
        pillars.add("reliability")
    if change_type == "security":
        outcomes.add("blocker-mitigation")
        pillars.add("security")
    if change_type == "pricing":
        outcomes.update({"consumption", "opportunity"})
        pillars.add("cost-optimization")
    if lifecycle in {"ga", "public-preview", "private-preview"} or change_type == "region-availability":
        outcomes.update({"architecture", "opportunity"})
    if technology in {"cosmos-db", "postgresql", "azure-sql", "aks", "app-service", "apim"}:
        pillars.add("performance-efficiency")

    return sorted(outcomes), sorted(pillars)


def action_text(change_type: str, lifecycle: str) -> tuple[str, str]:
    if change_type in {"deprecated", "retired", "breaking-change"}:
        return (
            "This can create a customer delivery blocker or migration requirement.",
            "Identify affected workloads, verify the effective date, and create a tested migration action.",
        )
    if change_type == "security":
        return (
            "This may change the workload security posture or required controls.",
            "Validate exposure, supported mitigations, and the customer's remediation owner.",
        )
    if change_type == "incident":
        return (
            "Service degradation can affect delivery confidence and operational readiness.",
            "Check live status and personalized Service Health before advising a customer.",
        )
    if lifecycle == "ga":
        return (
            "A generally available capability may remove a blocker or create an expansion opportunity.",
            "Confirm regional availability and evaluate it against active customer architectures.",
        )
    if lifecycle in {"public-preview", "private-preview"}:
        return (
            "A preview can inform roadmap and technical validation, but is not a production commitment.",
            "Review preview terms, regions, limitations, and support before proposing a customer pilot.",
        )
    return (
        "The change may affect current guidance, readiness material, or customer conversations.",
        "Review the canonical source and update reusable guidance when the change is relevant.",
    )
