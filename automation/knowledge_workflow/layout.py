"""Repository paths for The Azure Update knowledge workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True, frozen=True)
class RepositoryLayout:
    repository_root: Path

    @property
    def automation_root(self) -> Path:
        return self.repository_root / "automation"

    @property
    def config_dir(self) -> Path:
        return self.automation_root / "config"

    @property
    def state_dir(self) -> Path:
        return self.automation_root / "state"

    @property
    def reports_dir(self) -> Path:
        return self.automation_root / "reports"

    @property
    def daily_dir(self) -> Path:
        return self.reports_dir / "daily"

    @property
    def alerts_dir(self) -> Path:
        return self.reports_dir / "alerts"

    @property
    def hub_path(self) -> Path:
        return self.automation_root / "Hub.md"

    @property
    def knowledge_dir(self) -> Path:
        return self.repository_root / "knowledge"

    @property
    def posts_dir(self) -> Path:
        return self.repository_root / "src" / "posts"

    def website_post_path(self, as_of: datetime) -> Path:
        slug = f"azure-update-{as_of.date().isoformat()}"
        return self.posts_dir / slug / "index.md"
