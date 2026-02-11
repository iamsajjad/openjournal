"""Cryptographic utilities for secret generation."""

from __future__ import annotations

import secrets

from src.config.models import InstanceSecrets
from src.constants import (
    DEFAULT_API_KEY_LENGTH,
    DEFAULT_DB_SECRET_LENGTH,
    DEFAULT_SALT_LENGTH,
)


def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_instance_secrets() -> InstanceSecrets:
    """Generate all cryptographic secrets needed for an OJS instance."""
    return InstanceSecrets(
        db_password=generate_secret(DEFAULT_DB_SECRET_LENGTH),
        db_root_password=generate_secret(DEFAULT_DB_SECRET_LENGTH),
        salt=generate_secret(DEFAULT_SALT_LENGTH),
        api_key_secret=generate_secret(DEFAULT_API_KEY_LENGTH),
    )
