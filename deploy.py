#!/usr/bin/env python3
"""OJS Multi-Site Deployment Script.

Reimplements deploy.sh entirely in Python with production-grade quality.
Creates a new OJS instance from the 'journal' template for a specific domain.

Usage:
    python3 deploy.py <domain> [--locale LOCALE] [--email EMAIL]
                                [--force] [--dry-run] [--log-level LEVEL]

Example:
    python3 deploy.py ejournal.example.com
    python3 deploy.py ejournal.example.com --locale ar --email admin@example.com
    python3 deploy.py ejournal.example.com --force --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPLATE_DIR = "journal"

# OJS runs as www-data (uid 33, gid 33)
WWW_DATA_UID = 33
WWW_DATA_GID = 33

# MariaDB runs as mysql (uid 999, gid 999)
MYSQL_UID = 999
MYSQL_GID = 999

# Exit codes
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_PERMISSION_ERROR = 2

# Placeholder tokens used in template files
TOKEN_DOMAIN     = "{{DOMAIN}}"
TOKEN_JOURNAL    = "{{JOURNAL}}"
TOKEN_DATABASE   = "{{DATABASE}}"
TOKEN_DB_HOST    = "{{DB_HOST}}"
TOKEN_ACME_EMAIL = "{{ACME_EMAIL}}"
TOKEN_LOCALE     = "{{LOCALE}}"

log = logging.getLogger("deploy")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _configure_logging(level: str) -> None:
    """Set up structured logging to stderr."""
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        print(f"Invalid log level: {level}", file=sys.stderr)
        sys.exit(EXIT_USER_ERROR)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


def _extract_subdomain(domain: str) -> str:
    """Extract the first label from a FQDN (e.g. 'journal1.example.com' → 'journal1')."""
    return domain.split(".")[0]


def _chown_recursive(path: Path, uid: int, gid: int, *, dry_run: bool) -> None:
    """Recursively change ownership of *path* to *uid*:*gid*."""
    if dry_run:
        log.info("[DRY-RUN] Would chown -R %d:%d %s", uid, gid, path)
        return

    for dirpath, dirnames, filenames in os.walk(path):
        os.chown(dirpath, uid, gid)
        for name in dirnames + filenames:
            os.chown(os.path.join(dirpath, name), uid, gid)


def _has_privilege() -> bool:
    """Return True if current process can change file ownership.

    Checks for:
      - Running as root (EUID 0)
      - Membership in sudo/wheel groups (best-effort)
    """
    if os.geteuid() == 0:
        return True

    try:
        import grp
        user_groups = {grp.getgrgid(g).gr_name for g in os.getgroups()}
        return bool(user_groups & {"sudo", "wheel"})
    except (KeyError, ImportError):
        return False


def _replace_in_file(
    filepath: Path,
    replacements: list[tuple[str, str]],
    *,
    dry_run: bool,
) -> None:
    """Apply a list of (old, new) string replacements to a file.

    Reads the file, applies all replacements, writes back.
    Secrets are never logged — only the file path and replacement count.
    """
    if not filepath.exists():
        log.warning("File not found, skipping: %s", filepath)
        return

    content = filepath.read_text(encoding="utf-8")
    count = 0
    for old, new in replacements:
        occurrences = content.count(old)
        if occurrences:
            content = content.replace(old, new)
            count += occurrences

    if dry_run:
        log.info("[DRY-RUN] Would apply %d replacements in %s", count, filepath)
        return

    filepath.write_text(content, encoding="utf-8")
    log.info("✓ Applied %d replacements in %s", count, filepath)


# ---------------------------------------------------------------------------
# Core deployment steps
# ---------------------------------------------------------------------------

def validate_environment(template_dir: Path) -> None:
    """Validate that the template directory exists and contains expected files."""
    if not template_dir.is_dir():
        log.error("Template directory '%s' not found!", template_dir)
        sys.exit(EXIT_USER_ERROR)

    expected = [".env", "compose.yml"]
    for name in expected:
        if not (template_dir / name).exists():
            log.warning("Expected template file missing: %s/%s", template_dir, name)


def handle_existing_target(target_dir: Path, *, force: bool, dry_run: bool) -> None:
    """If *target_dir* already exists, prompt for overwrite or abort."""
    if not target_dir.exists():
        return

    if dry_run:
        log.info("[DRY-RUN] Directory '%s' exists; would prompt/overwrite.", target_dir)
        return

    if force:
        log.info("Directory '%s' exists — overwriting (--force).", target_dir)
        shutil.rmtree(target_dir)
        return

    log.warning("Directory '%s' already exists.", target_dir)
    try:
        reply = input("Do you want to overwrite it? (y/n) ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        log.info("Aborted.")
        sys.exit(EXIT_USER_ERROR)

    if reply not in ("y", "yes"):
        log.info("Aborted.")
        sys.exit(EXIT_USER_ERROR)

    shutil.rmtree(target_dir)


def copy_template(template_dir: Path, target_dir: Path, *, dry_run: bool) -> None:
    """Copy the template directory to the target location."""
    if dry_run:
        log.info("[DRY-RUN] Would copy '%s' → '%s'", template_dir, target_dir)
        return

    shutil.copytree(template_dir, target_dir)
    log.info("✓ Created directory: %s", target_dir)


def configure_env(
    env_file: Path,
    domain: str,
    acme_email: str,
    subdomain: str,
    *,
    dry_run: bool,
) -> None:
    """Replace placeholders and update DB_HOST in the .env file."""
    _replace_in_file(
        env_file,
        [
            (TOKEN_DOMAIN, domain),
            (TOKEN_ACME_EMAIL, acme_email),
            (TOKEN_DB_HOST, f"db-{subdomain}"),
        ],
        dry_run=dry_run,
    )


def configure_config_inc(
    config_file: Path,
    domain: str,
    locale: str,
    subdomain: str,
    *,
    dry_run: bool,
) -> None:
    """Replace placeholders in config.inc.php."""
    _replace_in_file(
        config_file,
        [
            (TOKEN_DOMAIN, domain),
            (TOKEN_LOCALE, locale),
            (TOKEN_DB_HOST, f"db-{subdomain}"),
        ],
        dry_run=dry_run,
    )


def configure_compose(
    compose_file: Path,
    subdomain: str,
    *,
    dry_run: bool,
) -> None:
    """Rename services and Traefik routers in compose.yml to avoid collisions."""
    _replace_in_file(
        compose_file,
        [
            # Service names (preserve leading indent)
            (TOKEN_JOURNAL,  f"journal-{subdomain}"),
            (TOKEN_DATABASE, f"db-{subdomain}"),
        ],
        dry_run=dry_run,
    )


def set_permissions(target_dir: Path, *, dry_run: bool) -> None:
    """Create required directories and set ownership for Docker volumes.

    - volumes/*  → 33:33  (www-data, for OJS)
    - volumes/db → 999:999 (mysql, for MariaDB)
    """
    volumes_dir = target_dir / "volumes"
    db_dir = volumes_dir / "db"

    if not _has_privilege():
        log.error("Access denied: You must be root or a member of the sudo/wheel group.")
        log.error("Please manually run:")
        log.error("  chown -R %d:%d %s", WWW_DATA_UID, WWW_DATA_GID, volumes_dir)
        log.error("  chown -R %d:%d %s", MYSQL_UID, MYSQL_GID, db_dir)
        sys.exit(EXIT_PERMISSION_ERROR)

    # Set www-data ownership on all volumes
    _chown_recursive(volumes_dir, WWW_DATA_UID, WWW_DATA_GID, dry_run=dry_run)

    # Override: set mysql ownership on the database directory
    _chown_recursive(db_dir, MYSQL_UID, MYSQL_GID, dry_run=dry_run)

    if not dry_run:
        log.info("✓ Permissions set")


def print_summary(domain: str, target_dir: Path) -> None:
    """Print post-deployment instructions."""
    print(f"\n--- Deployment Ready: {domain} ---\n")
    print("1. Enter directory:")
    print(f"   -> cd {target_dir}\n")
    print("2. Start containers:")
    print("   -> cd docker compose up -d\n")
    print("3. Visit:")
    print(f"   -> https://{domain}\n")
    print("--- Journal Deployment Complete ---")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        description="OJS Multi-Site Deployment — create a new journal instance from template.",
        epilog="Example: python3 deploy.py journal1.example.com --locale ar",
    )
    parser.add_argument(
        "domain",
        help="Fully qualified domain name (e.g. journal1.example.com)",
    )
    parser.add_argument(
        "--locale",
        default="en",
        help="OJS locale code (default: en)",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="ACME / Let's Encrypt email (default: admin@<domain>)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target directory without prompting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview all operations without modifying the filesystem",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    _configure_logging(args.log_level)

    domain: str = args.domain
    locale: str = args.locale
    acme_email: str = args.email or f"admin@{domain}"
    force: bool = args.force
    dry_run: bool = args.dry_run

    # Resolve paths relative to this script's location (not cwd)
    script_dir = Path(__file__).resolve().parent
    template_dir = script_dir / TEMPLATE_DIR
    subdomain = _extract_subdomain(domain)
    target_dir = script_dir / subdomain

    log.debug("Domain      : %s", domain)
    log.debug("Subdomain   : %s", subdomain)
    log.debug("Locale      : %s", locale)
    log.debug("ACME email  : %s", acme_email)
    log.debug("Template    : %s", template_dir)
    log.debug("Target      : %s", target_dir)
    log.debug("Force       : %s", force)
    log.debug("Dry-run     : %s", dry_run)

    # --- Validate --------------------------------------------------------
    validate_environment(template_dir)

    # --- Handle existing target ------------------------------------------
    handle_existing_target(target_dir, force=force, dry_run=dry_run)

    log.info("Deploying %s to %s ...", domain, target_dir.name)

    # --- Step 1: Copy template -------------------------------------------
    copy_template(template_dir, target_dir, dry_run=dry_run)

    # --- Step 2: Configure .env ------------------------------------------
    configure_env(
        target_dir / ".env",
        domain,
        acme_email,
        subdomain,
        dry_run=dry_run,
    )

    # --- Step 3: Configure config.inc.php --------------------------------
    configure_config_inc(
        target_dir / "volumes" / "config" / "config.inc.php",
        domain,
        locale,
        subdomain,
        dry_run=dry_run,
    )

    # --- Step 4: Rename services in compose.yml --------------------------
    configure_compose(
        target_dir / "compose.yml",
        subdomain,
        dry_run=dry_run,
    )

    # --- Step 5: Set permissions -----------------------------------------
    set_permissions(target_dir, dry_run=dry_run)

    # --- Done ------------------------------------------------------------
    if not dry_run:
        print_summary(domain, Path(subdomain))
    else:
        log.info("[DRY-RUN] Deployment preview complete. No changes were made.")

    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(EXIT_USER_ERROR)
    except Exception as exc:
        log.error("Fatal error: %s", exc, exc_info=log.isEnabledFor(logging.DEBUG))
        sys.exit(EXIT_USER_ERROR)
