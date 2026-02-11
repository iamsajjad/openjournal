"""OJS configuration (config.inc.php) service."""

from __future__ import annotations

from pathlib import Path

from src.constants import (
    TOKEN_API_KEY_SECRET,
    TOKEN_DB_HOST,
    TOKEN_DB_PASSWORD,
    TOKEN_DOMAIN,
    TOKEN_LOCALE,
    TOKEN_SALT,
)
from src.utils.filesystem import replace_in_file


def configure_ojs(
    config_file: Path,
    domain: str,
    locale: str,
    subdomain: str,
    db_password: str,
    salt: str,
    api_key_secret: str,
    *,
    dry_run: bool,
) -> None:
    """Replace placeholders in config.inc.php."""
    replace_in_file(
        config_file,
        [
            (TOKEN_DOMAIN, domain),
            (TOKEN_LOCALE, locale),
            (TOKEN_DB_HOST, f"db-{subdomain}"),
            (TOKEN_DB_PASSWORD, db_password),
            (TOKEN_SALT, salt),
            (TOKEN_API_KEY_SECRET, api_key_secret),
        ],
        dry_run=dry_run,
    )
