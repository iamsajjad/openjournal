"""Tests for data models."""

from __future__ import annotations

import pytest

from src.config.models import DeploymentConfig, InstanceSecrets


class TestDeploymentConfig:
    """Tests for DeploymentConfig."""

    def test_stores_all_fields(self) -> None:
        config = DeploymentConfig(
            domain="j.example.com",
            locale="ar",
            acme_email="a@b.com",
            force=True,
            dry_run=True,
        )
        assert config.domain == "j.example.com"
        assert config.locale == "ar"
        assert config.acme_email == "a@b.com"
        assert config.force is True
        assert config.dry_run is True

    def test_frozen_prevents_mutation(self) -> None:
        config = DeploymentConfig(
            domain="example.com",
            locale="en",
            acme_email="admin@example.com",
            force=False,
            dry_run=False,
        )
        with pytest.raises(AttributeError):
            config.domain = "other.com"  # type: ignore[misc]


class TestInstanceSecrets:
    """Tests for InstanceSecrets."""

    def test_stores_all_fields(self) -> None:
        secrets = InstanceSecrets(
            db_password="a",
            db_root_password="b",
            salt="c",
            api_key_secret="d",
        )
        assert secrets.db_password == "a"
        assert secrets.db_root_password == "b"
        assert secrets.salt == "c"
        assert secrets.api_key_secret == "d"

    def test_frozen_prevents_mutation(self) -> None:
        secrets = InstanceSecrets(
            db_password="a",
            db_root_password="b",
            salt="c",
            api_key_secret="d",
        )
        with pytest.raises(AttributeError):
            secrets.db_password = "x"  # type: ignore[misc]
