"""Filesystem utilities for deployment operations."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from src.exceptions import OwnershipError, TemplateError

log = logging.getLogger(__name__)


def replace_in_file(
    filepath: Path,
    replacements: list[tuple[str, str]],
    *,
    dry_run: bool,
) -> int:
    """Apply string replacements to a file.

    Raises:
        TemplateError: If the file cannot be read or written.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.warning("File not found, skipping: %s", filepath)
        return 0
    except OSError as exc:
        raise TemplateError(f"Failed to read {filepath}: {exc}") from exc

    count = 0
    for old, new in replacements:
        occurrences = content.count(old)
        if occurrences:
            content = content.replace(old, new)
            count += occurrences

    if count == 0:
        log.warning("No tokens found in %s — file may be misconfigured", filepath)

    if dry_run:
        log.info("[DRY-RUN] Would apply %d replacements in %s", count, filepath)
        return count

    try:
        filepath.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"Failed to write {filepath}: {exc}") from exc

    log.info("[OK] Applied %d replacements in %s", count, filepath)
    return count


def copy_template(template_dir: Path, target_dir: Path, *, dry_run: bool) -> None:
    """Copy the template directory to the target location.

    Raises:
        TemplateError: If the copy operation fails.
    """
    if dry_run:
        log.info("[DRY-RUN] Would copy '%s' → '%s'", template_dir, target_dir)
        return

    try:
        shutil.copytree(template_dir, target_dir)
    except OSError as exc:
        raise TemplateError(
            f"Failed to copy template '{template_dir}' to '{target_dir}': {exc}"
        ) from exc

    log.info("[OK] Created directory: %s", target_dir)


def chown_recursive(path: Path, uid: int, gid: int, *, dry_run: bool) -> None:
    """Recursively change ownership of a directory tree.

    Raises:
        OwnershipError: If ownership change fails.
    """
    if dry_run:
        log.info("[DRY-RUN] Would chown -R %d:%d %s", uid, gid, path)
        return

    try:
        for dirpath, dirnames, filenames in os.walk(path):
            os.chown(dirpath, uid, gid)
            for name in dirnames + filenames:
                os.chown(os.path.join(dirpath, name), uid, gid)
    except OSError as exc:
        raise OwnershipError(f"Failed to set ownership {uid}:{gid} on {path}: {exc}") from exc


def has_privilege() -> bool:
    """Return True if running as root (euid == 0)."""
    return os.geteuid() == 0


def remove_directory(path: Path) -> None:
    """Remove a directory tree.

    Raises:
        TemplateError: If removal fails.
    """
    try:
        shutil.rmtree(path)
    except OSError as exc:
        raise TemplateError(f"Failed to remove directory '{path}': {exc}") from exc
