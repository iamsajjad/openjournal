"""Docker Compose configuration service."""

from __future__ import annotations

from pathlib import Path

from src.constants import TOKEN_DATABASE, TOKEN_JOURNAL
from src.utils.filesystem import replace_in_file


def configure_compose(
    compose_file: Path,
    subdomain: str,
    *,
    dry_run: bool,
) -> None:
    """Replace template tokens with subdomain-specific service names in compose.yml."""
    replace_in_file(
        compose_file,
        [
            (TOKEN_JOURNAL, f"journal-{subdomain}"),
            (TOKEN_DATABASE, f"db-{subdomain}"),
        ],
        dry_run=dry_run,
    )
