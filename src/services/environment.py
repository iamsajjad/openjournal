"""Environment file (.env) configuration service."""

from __future__ import annotations

from pathlib import Path

from src.constants import (
    TOKEN_ACME_EMAIL,
    TOKEN_DB_HOST,
    TOKEN_DB_PASSWORD,
    TOKEN_DB_ROOT_PASSWORD,
    TOKEN_DOMAIN,
)
from src.utils.filesystem import replace_in_file


def configure_env(
    env_file: Path,
    domain: str,
    acme_email: str,
    subdomain: str,
    db_password: str,
    db_root_password: str,
    *,
    dry_run: bool,
) -> None:
    """Replace placeholders in the .env file."""
    replace_in_file(
        env_file,
        [
            (TOKEN_DOMAIN, domain),
            (TOKEN_ACME_EMAIL, acme_email),
            (TOKEN_DB_HOST, f"db-{subdomain}"),
            (TOKEN_DB_PASSWORD, db_password),
            (TOKEN_DB_ROOT_PASSWORD, db_root_password),
        ],
        dry_run=dry_run,
    )
