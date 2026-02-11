"""Tests for cryptographic utilities."""

from __future__ import annotations

from src.config.models import InstanceSecrets
from src.utils.crypto import generate_instance_secrets, generate_secret


class TestGenerateSecret:
    """Tests for generate_secret."""

    def test_returns_string(self) -> None:
        assert isinstance(generate_secret(), str)

    def test_non_empty(self) -> None:
        assert len(generate_secret()) > 0

    def test_unique_across_calls(self) -> None:
        generated = {generate_secret() for _ in range(100)}
        assert len(generated) == 100

    def test_longer_length_produces_longer_output(self) -> None:
        short = generate_secret(8)
        long = generate_secret(64)
        assert len(short) < len(long)


class TestGenerateInstanceSecrets:
    """Tests for generate_instance_secrets."""

    def test_returns_instance_secrets(self) -> None:
        result = generate_instance_secrets()
        assert isinstance(result, InstanceSecrets)

    def test_all_fields_populated(self) -> None:
        result = generate_instance_secrets()
        assert result.db_password
        assert result.db_root_password
        assert result.salt
        assert result.api_key_secret

    def test_all_fields_are_unique(self) -> None:
        result = generate_instance_secrets()
        values = [
            result.db_password,
            result.db_root_password,
            result.salt,
            result.api_key_secret,
        ]
        assert len(set(values)) == len(values)
