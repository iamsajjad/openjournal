#!/usr/bin/env python3
"""OJS Multi-Site Deployment Script.

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
import sys
from pathlib import Path

from src.config.models import DeploymentConfig
from src.constants import ExitCode
from src.core.deployer import Deployer, resolve_paths
from src.exceptions import DeploymentError, DomainValidationError
from src.utils.crypto import generate_instance_secrets

log = logging.getLogger("deploy")


def _configure_logging(level: str) -> None:
    """Set up structured logging to stderr."""
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        print(f"Invalid log level: {level}", file=sys.stderr)
        sys.exit(ExitCode.USER_ERROR)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


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
    acme_email: str = args.email or f"admin@{domain}"
    script_dir = Path(__file__).resolve().parent

    try:
        paths = resolve_paths(domain, script_dir)
    except DomainValidationError as exc:
        log.error("%s", exc)
        return ExitCode.USER_ERROR

    config = DeploymentConfig(
        domain=domain,
        locale=args.locale,
        acme_email=acme_email,
        force=args.force,
        dry_run=args.dry_run,
    )

    secrets = generate_instance_secrets()

    log.debug("Domain      : %s", config.domain)
    log.debug("Subdomain   : %s", paths.subdomain)
    log.debug("Locale      : %s", config.locale)
    log.debug("ACME email  : %s", config.acme_email)
    log.debug("Template    : %s", paths.template_dir)
    log.debug("Target      : %s", paths.target_dir)
    log.debug("Force       : %s", config.force)
    log.debug("Dry-run     : %s", config.dry_run)

    deployer = Deployer(config=config, paths=paths, secrets=secrets)

    try:
        deployer.deploy()
    except DeploymentError as exc:
        log.error("%s", exc)
        return ExitCode.USER_ERROR

    return ExitCode.SUCCESS


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(ExitCode.USER_ERROR)
    except Exception as exc:
        log.error("Fatal error: %s", exc, exc_info=log.isEnabledFor(logging.DEBUG))
        sys.exit(ExitCode.USER_ERROR)
