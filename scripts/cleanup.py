#!/usr/bin/env python3
"""Docker Cleanup Script.

Removes all Docker resources (containers, images, volumes, and networks)
to reset the environment.

WARNING: This script is DESTRUCTIVE. All data in Docker volumes will be
permanently lost.

Usage:
    python3 scripts/cleanup.py
"""

from __future__ import annotations

import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger("cleanup")


def _run_command(command: list[str]) -> str | None:
    """Run a command and return stripped stdout, or None on failure."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        log.warning("Command failed: %s — %s", " ".join(command), exc.stderr.strip())
        return None


def clean_docker() -> None:
    """Remove all Docker containers, images, volumes, and custom networks."""
    log.warning("This will delete ALL Docker containers, images, volumes, and networks.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")

    if confirm.lower() != "yes":
        log.info("Operation cancelled.")
        return

    log.info("--- Starting Docker Cleanup ---")

    log.info("1. Stopping and removing all containers...")
    ids = _run_command(["docker", "ps", "-aq"])
    if ids:
        _run_command(["docker", "stop"] + ids.split())
        _run_command(["docker", "rm"] + ids.split())
        log.info("   -> Containers stopped and removed.")
    else:
        log.info("   -> No containers found.")

    log.info("2. Removing all images...")
    ids = _run_command(["docker", "images", "-q"])
    if ids:
        _run_command(["docker", "rmi", "-f"] + ids.split())
        log.info("   -> Images removed.")
    else:
        log.info("   -> No images found.")

    log.info("3. Removing all volumes...")
    ids = _run_command(["docker", "volume", "ls", "-q"])
    if ids:
        _run_command(["docker", "volume", "rm"] + ids.split())
        log.info("   -> Volumes removed.")
    else:
        log.info("   -> No volumes found.")

    log.info("4. Removing custom networks...")
    _run_command(["docker", "network", "prune", "-f"])
    log.info("   -> Unused networks removed.")

    log.info("--- Cleanup Complete ---")


if __name__ == "__main__":
    clean_docker()
