"""Main deployment orchestrator for OJS instances."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config.models import DeploymentConfig, DeploymentPaths, InstanceSecrets
from src.config.validators import extract_subdomain, validate_domain
from src.constants import TEMPLATE_DIR
from src.exceptions import DeploymentError
from src.services.compose import configure_compose
from src.services.environment import configure_env
from src.services.ojs import configure_ojs
from src.services.permissions import set_permissions
from src.utils.filesystem import copy_template, remove_directory

log = logging.getLogger(__name__)


class Deployer:
    """Orchestrates the deployment of a new OJS instance."""

    def __init__(
        self,
        config: DeploymentConfig,
        paths: DeploymentPaths,
        secrets: InstanceSecrets,
    ) -> None:
        self._config = config
        self._paths = paths
        self._secrets = secrets

    def deploy(self) -> None:
        """Execute the full deployment pipeline.

        Raises:
            DeploymentError: If any deployment step fails.
        """
        self._validate_template()
        self._handle_existing_target()

        log.info(
            "Deploying %s to %s ...",
            self._config.domain,
            self._paths.target_dir.name,
        )

        self._copy_template()
        self._configure_env()
        self._configure_ojs()
        self._configure_compose()
        set_permissions(self._paths.target_dir, dry_run=self._config.dry_run)

        if not self._config.dry_run:
            self._print_summary()
        else:
            log.info("[DRY-RUN] Deployment preview complete. No changes were made.")

    def _validate_template(self) -> None:
        """Verify the template directory exists and contains expected files."""
        template_dir = self._paths.template_dir
        if not template_dir.is_dir():
            raise DeploymentError(f"Template directory '{template_dir}' not found!")

        expected = [".env", "compose.yml"]
        for name in expected:
            if not (template_dir / name).exists():
                log.warning("Expected template file missing: %s/%s", template_dir, name)

    def _handle_existing_target(self) -> None:
        """Handle pre-existing target directory."""
        target_dir = self._paths.target_dir
        if not target_dir.exists():
            return

        if self._config.dry_run:
            log.info(
                "[DRY-RUN] Directory '%s' exists; would prompt/overwrite.",
                target_dir,
            )
            return

        if self._config.force:
            log.info("Directory '%s' exists — overwriting (--force).", target_dir)
            remove_directory(target_dir)
            return

        log.warning("Directory '%s' already exists.", target_dir)
        try:
            reply = input("Do you want to overwrite it? (y/n) ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise DeploymentError("Aborted by user.")

        if reply not in ("y", "yes"):
            raise DeploymentError("Aborted by user.")

        remove_directory(target_dir)

    def _copy_template(self) -> None:
        """Copy template directory to target location."""
        copy_template(
            self._paths.template_dir,
            self._paths.target_dir,
            dry_run=self._config.dry_run,
        )

    def _configure_env(self) -> None:
        """Configure the .env file with deployment values."""
        configure_env(
            self._paths.target_dir / ".env",
            self._config.domain,
            self._config.acme_email,
            self._paths.subdomain,
            self._secrets.db_password,
            self._secrets.db_root_password,
            dry_run=self._config.dry_run,
        )

    def _configure_ojs(self) -> None:
        """Configure config.inc.php with deployment values."""
        configure_ojs(
            self._paths.target_dir / "volumes" / "config" / "config.inc.php",
            self._config.domain,
            self._config.locale,
            self._paths.subdomain,
            self._secrets.db_password,
            self._secrets.salt,
            self._secrets.api_key_secret,
            dry_run=self._config.dry_run,
        )

    def _configure_compose(self) -> None:
        """Configure compose.yml with subdomain-specific service names."""
        configure_compose(
            self._paths.target_dir / "compose.yml",
            self._paths.subdomain,
            dry_run=self._config.dry_run,
        )

    def _print_summary(self) -> None:
        """Log post-deployment instructions."""
        domain = self._config.domain
        target = self._paths.subdomain
        log.info("")
        log.info("--- Deployment Ready: %s ---", domain)
        log.info("")
        log.info("1. Enter directory:")
        log.info("   -> cd %s", target)
        log.info("")
        log.info("2. Start containers:")
        log.info("   -> docker compose up -d")
        log.info("")
        log.info("3. Visit:")
        log.info("   -> https://%s", domain)
        log.info("")
        log.info("--- Journal Deployment Complete ---")


def resolve_paths(domain: str, script_dir: Path) -> DeploymentPaths:
    """Validate domain and resolve filesystem paths for a deployment.

    Raises:
        DomainValidationError: If the domain is invalid.
    """
    validate_domain(domain)
    subdomain = extract_subdomain(domain)
    return DeploymentPaths(
        script_dir=script_dir,
        template_dir=script_dir / TEMPLATE_DIR,
        target_dir=script_dir / subdomain,
        subdomain=subdomain,
    )
