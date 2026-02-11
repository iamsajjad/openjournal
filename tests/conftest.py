"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config.models import DeploymentConfig, DeploymentPaths, InstanceSecrets


@pytest.fixture
def sample_config() -> DeploymentConfig:
    """Provide a sample deployment configuration in dry-run mode."""
    return DeploymentConfig(
        domain="ejournal.example.com",
        locale="en",
        acme_email="admin@example.com",
        force=False,
        dry_run=True,
    )


@pytest.fixture
def sample_secrets() -> InstanceSecrets:
    """Provide deterministic instance secrets for testing."""
    return InstanceSecrets(
        db_password="test-db-password",
        db_root_password="test-db-root-password",
        salt="test-salt-value",
        api_key_secret="test-api-key-secret",
    )


@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    """Create a minimal journal template directory structure."""
    journal = tmp_path / "journal"
    journal.mkdir()

    (journal / ".env").write_text(
        "DOMAIN={{DOMAIN}}\n"
        "DB_HOST={{DB_HOST}}\n"
        "DB_PASSWORD={{DB_PASSWORD}}\n"
        "DB_ROOT_PASSWORD={{DB_ROOT_PASSWORD}}\n"
        "ACME_EMAIL={{ACME_EMAIL}}\n"
    )
    (journal / "compose.yml").write_text(
        "services:\n"
        "  {{JOURNAL}}:\n"
        "    image: ojs\n"
        "  {{DATABASE}}:\n"
        "    image: mariadb\n"
    )

    config_dir = journal / "volumes" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "config.inc.php").write_text(
        'base_url = "https://{{DOMAIN}}"\n'
        "host = {{DB_HOST}}\n"
        "password = {{DB_PASSWORD}}\n"
        "locale = {{LOCALE}}\n"
        'salt = "{{SALT}}"\n'
        'api_key_secret = "{{API_KEY_SECRET}}"\n'
    )

    (journal / "volumes" / "db").mkdir(parents=True)
    (journal / "volumes" / "files").mkdir(parents=True)
    (journal / "volumes" / "public").mkdir(parents=True)

    return journal


@pytest.fixture
def sample_paths(tmp_path: Path, template_dir: Path) -> DeploymentPaths:
    """Provide sample deployment paths using a temporary directory."""
    return DeploymentPaths(
        script_dir=tmp_path,
        template_dir=template_dir,
        target_dir=tmp_path / "ejournal",
        subdomain="ejournal",
    )
