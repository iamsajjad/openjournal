"""Tests for deployment orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.models import DeploymentConfig, DeploymentPaths, InstanceSecrets
from src.core.deployer import Deployer, resolve_paths
from src.exceptions import DeploymentError, DomainValidationError


class TestResolvePaths:
    """Tests for resolve_paths."""

    def test_resolves_subdomain_and_paths(self, tmp_path: Path) -> None:
        (tmp_path / "journal").mkdir()
        paths = resolve_paths("ejournal.example.com", tmp_path)
        assert paths.subdomain == "ejournal"
        assert paths.template_dir == tmp_path / "journal"
        assert paths.target_dir == tmp_path / "ejournal"
        assert paths.script_dir == tmp_path

    def test_invalid_domain_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DomainValidationError):
            resolve_paths("..com", tmp_path)


class TestDeployer:
    """Tests for Deployer."""

    def test_dry_run_does_not_create_target(
        self,
        sample_config: DeploymentConfig,
        sample_paths: DeploymentPaths,
        sample_secrets: InstanceSecrets,
    ) -> None:
        deployer = Deployer(
            config=sample_config,
            paths=sample_paths,
            secrets=sample_secrets,
        )
        deployer.deploy()
        assert not sample_paths.target_dir.exists()

    @patch("src.services.permissions.chown_recursive")
    @patch("src.services.permissions.has_privilege", return_value=True)
    def test_real_deployment_creates_target(
        self,
        _mock_priv: object,
        _mock_chown: object,
        sample_paths: DeploymentPaths,
        sample_secrets: InstanceSecrets,
    ) -> None:
        config = DeploymentConfig(
            domain="ejournal.example.com",
            locale="en",
            acme_email="admin@example.com",
            force=False,
            dry_run=False,
        )
        deployer = Deployer(config=config, paths=sample_paths, secrets=sample_secrets)
        deployer.deploy()

        assert sample_paths.target_dir.exists()
        assert (sample_paths.target_dir / ".env").exists()
        assert (sample_paths.target_dir / "compose.yml").exists()

    def test_missing_template_raises(
        self,
        sample_secrets: InstanceSecrets,
        tmp_path: Path,
    ) -> None:
        config = DeploymentConfig(
            domain="ejournal.example.com",
            locale="en",
            acme_email="admin@example.com",
            force=False,
            dry_run=True,
        )
        paths = DeploymentPaths(
            script_dir=tmp_path,
            template_dir=tmp_path / "nonexistent",
            target_dir=tmp_path / "ejournal",
            subdomain="ejournal",
        )
        deployer = Deployer(config=config, paths=paths, secrets=sample_secrets)

        with pytest.raises(DeploymentError, match="not found"):
            deployer.deploy()


class TestDeployerTokenReplacement:
    """Verify tokens are replaced in generated config files."""

    @patch("src.services.permissions.chown_recursive")
    @patch("src.services.permissions.has_privilege", return_value=True)
    def test_env_tokens_replaced(
        self,
        _mock_priv: object,
        _mock_chown: object,
        sample_paths: DeploymentPaths,
        sample_secrets: InstanceSecrets,
    ) -> None:
        config = DeploymentConfig(
            domain="ejournal.example.com",
            locale="en",
            acme_email="admin@example.com",
            force=False,
            dry_run=False,
        )
        Deployer(config=config, paths=sample_paths, secrets=sample_secrets).deploy()

        env_content = (sample_paths.target_dir / ".env").read_text()
        assert "{{DOMAIN}}" not in env_content
        assert "ejournal.example.com" in env_content
        assert "db-ejournal" in env_content

    @patch("src.services.permissions.chown_recursive")
    @patch("src.services.permissions.has_privilege", return_value=True)
    def test_compose_tokens_replaced(
        self,
        _mock_priv: object,
        _mock_chown: object,
        sample_paths: DeploymentPaths,
        sample_secrets: InstanceSecrets,
    ) -> None:
        config = DeploymentConfig(
            domain="ejournal.example.com",
            locale="en",
            acme_email="admin@example.com",
            force=False,
            dry_run=False,
        )
        Deployer(config=config, paths=sample_paths, secrets=sample_secrets).deploy()

        compose_content = (sample_paths.target_dir / "compose.yml").read_text()
        assert "{{JOURNAL}}" not in compose_content
        assert "{{DATABASE}}" not in compose_content
        assert "journal-ejournal" in compose_content
        assert "db-ejournal" in compose_content
