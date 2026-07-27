"""Normalized records shared by collectors, validators, and renderers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse


TECHNOLOGIES = {
    "ai-foundry",
    "github",
    "quantum",
    "apim",
    "aks",
    "app-service",
    "cosmos-db",
    "postgresql",
    "azure-sql",
    "cross-cutting",
}

CONTENT_TYPES = {
    "docs",
    "update",
    "release-note",
    "status",
    "retirement",
    "security",
    "training",
    "sample",
    "architecture",
    "internal-guidance",
    "customer-pattern",
}

CHANGE_TYPES = {
    "new",
    "updated",
    "deprecated",
    "retired",
    "breaking-change",
    "known-issue",
    "incident",
    "maintenance",
    "region-availability",
    "pricing",
    "security",
    "no-change",
}

LIFECYCLES = {
    "in-development",
    "private-preview",
    "public-preview",
    "ga",
    "deprecated",
    "retired",
    "unknown",
}

IMPACT_LEVELS = {"critical", "high", "medium", "low", "none", "unknown"}
REVIEW_STATES = {"machine-draft", "human-reviewed", "superseded", "archived"}
SENSITIVITY_LEVELS = {"public", "internal", "confidential", "restricted"}


class ValidationError(ValueError):
    """Raised when a normalized knowledge item violates the content contract."""


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class KnowledgeItem:
    """A source-grounded change or guidance item."""

    id: str
    title: str
    technology: str
    content_type: str
    change_type: str
    lifecycle: str
    source_name: str
    source_url: str
    source_tier: int
    summary: str
    published_at: datetime | None = None
    observed_at: datetime = field(default_factory=utc_now)
    effective_at: datetime | None = None
    publisher: str = "Microsoft"
    customer_impact: str = "unknown"
    csa_outcomes: list[str] = field(default_factory=list)
    waf_pillars: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    sensitivity: str = "public"
    review_state: str = "machine-draft"
    external_id: str | None = None
    raw_categories: list[str] = field(default_factory=list)
    why_it_matters: str = ""
    recommended_action: str = ""
    supporting_urls: list[str] = field(default_factory=list)
    content_hash: str = ""

    def __post_init__(self) -> None:
        self.published_at = parse_datetime(self.published_at)
        self.observed_at = parse_datetime(self.observed_at) or utc_now()
        self.effective_at = parse_datetime(self.effective_at)
        self.validate()
        if not self.content_hash:
            self.content_hash = self.calculate_hash()

    def validate(self) -> None:
        errors: list[str] = []
        required = {
            "id": self.id,
            "title": self.title,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "summary": self.summary,
        }
        errors.extend(f"{name} is required" for name, value in required.items() if not value.strip())

        if self.technology not in TECHNOLOGIES:
            errors.append(f"unsupported technology: {self.technology}")
        if self.content_type not in CONTENT_TYPES:
            errors.append(f"unsupported content_type: {self.content_type}")
        if self.change_type not in CHANGE_TYPES:
            errors.append(f"unsupported change_type: {self.change_type}")
        if self.lifecycle not in LIFECYCLES:
            errors.append(f"unsupported lifecycle: {self.lifecycle}")
        if self.customer_impact not in IMPACT_LEVELS:
            errors.append(f"unsupported customer_impact: {self.customer_impact}")
        if self.review_state not in REVIEW_STATES:
            errors.append(f"unsupported review_state: {self.review_state}")
        if self.sensitivity not in SENSITIVITY_LEVELS:
            errors.append(f"unsupported sensitivity: {self.sensitivity}")
        if self.source_tier not in range(0, 5):
            errors.append("source_tier must be between 0 and 4")

        parsed_url = urlparse(self.source_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            errors.append("source_url must be an absolute HTTPS URL")

        if errors:
            raise ValidationError("; ".join(errors))

    def calculate_hash(self) -> str:
        normalized = "\n".join(
            [
                self.title.strip(),
                self.summary.strip(),
                self.source_url.strip(),
                self.lifecycle,
                self.change_type,
            ]
        )
        return f"sha256:{sha256(normalized.encode('utf-8')).hexdigest()}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["published_at"] = isoformat(self.published_at)
        data["observed_at"] = isoformat(self.observed_at)
        data["effective_at"] = isoformat(self.effective_at)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeItem":
        return cls(**data)
