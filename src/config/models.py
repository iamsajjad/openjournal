"""Data models for deployment configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeploymentConfig:
    """User-provided deployment parameters."""

    domain: str
    locale: str
    acme_email: str
    force: bool
    dry_run: bool


@dataclass(frozen=True)
class InstanceSecrets:
    """Cryptographically generated secrets for an OJS instance."""

    db_password: str
    db_root_password: str
    salt: str
    api_key_secret: str


@dataclass(frozen=True)
class DeploymentPaths:
    """Resolved filesystem paths for deployment."""

    script_dir: Path
    template_dir: Path
    target_dir: Path
    subdomain: str
