"""File permission and ownership service."""

from __future__ import annotations

import logging
from pathlib import Path

from src.constants import MYSQL_GID, MYSQL_UID, WWW_DATA_GID, WWW_DATA_UID
from src.exceptions import OwnershipError
from src.utils.filesystem import chown_recursive, has_privilege

log = logging.getLogger(__name__)


def set_permissions(target_dir: Path, *, dry_run: bool) -> None:
    """Set Docker volume ownership: www-data for OJS, mysql for MariaDB.

    Raises:
        OwnershipError: If not running as root.
    """
    volumes_dir = target_dir / "volumes"
    db_dir = volumes_dir / "db"

    if not dry_run and not has_privilege():
        raise OwnershipError(
            "Access denied: must run as root to set file ownership.\n"
            "Please run manually:\n"
            f"  sudo chown -R {WWW_DATA_UID}:{WWW_DATA_GID} {volumes_dir}\n"
            f"  sudo chown -R {MYSQL_UID}:{MYSQL_GID} {db_dir}"
        )

    chown_recursive(volumes_dir, WWW_DATA_UID, WWW_DATA_GID, dry_run=dry_run)
    chown_recursive(db_dir, MYSQL_UID, MYSQL_GID, dry_run=dry_run)

    if not dry_run:
        log.info("[OK] Permissions set")
