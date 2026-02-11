#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name:  docker_cleanup.py
Description:  Automates the removal of all Docker resources (containers, images,
              volumes, and networks) to reset the environment.

              WARNING: This script is DESTRUCTIVE. All data in Docker
              volumes will be permanently lost.

Usage:        Run with 'python3 cleanup.py' or './cleanup.py'
Dependencies: Requires Docker to be installed and running.
"""

import subprocess
import sys

def run_command(command):
    """Runs a system command and returns the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Ignore errors if no resources are found (e.g., trying to stop 0 containers)
        return None

def clean_docker():
    print("WARNING: This will delete ALL Docker containers, images, volumes, and networks.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")

    if confirm.lower() != "yes":
        print("Operation cancelled.")
        sys.exit()

    print("\n--- Starting Docker Cleanup ---\n")

    # 1. Stop all containers
    print("1. Stopping all containers...")
    ids = run_command("docker ps -aq")
    if ids:
        run_command(f"docker stop {ids}")
        print("   -> Containers stopped.")
    else:
        print("   -> No running containers found.")

    # 2. Remove all containers
    print("2. Removing all containers...")
    ids = run_command("docker ps -aq")
    if ids:
        run_command(f"docker rm {ids}")
        print("   -> Containers removed.")
    else:
        print("   -> No containers found to remove.")

    # 3. Remove all images
    print("3. Removing all images...")
    ids = run_command("docker images -q")
    if ids:
        # Force removal is often needed if images are tagged in multiple repositories
        run_command(f"docker rmi -f {ids}")
        print("   -> Images removed.")
    else:
        print("   -> No images found.")

    # 4. Remove all volumes
    print("4. Removing all volumes...")
    ids = run_command("docker volume ls -q")
    if ids:
        run_command(f"docker volume rm {ids}")
        print("   -> Volumes removed.")
    else:
        print("   -> No volumes found.")

    # 5. Remove all networks (excluding defaults)
    print("5. Removing custom networks...")
    # Docker prevents removing default networks (bridge, host, none), so we use 'prune'
    run_command("docker network prune -f")
    print("   -> Unused networks removed.")

    print("\n--- Cleanup Complete ---")

if __name__ == "__main__":
    clean_docker()
