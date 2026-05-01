#!/usr/bin/env python3
"""Run a database backup and upload to GitHub Releases.

Usage (from project root):
    python scripts/backup.py

Required environment variables:
    DATABASE_URL       — PostgreSQL connection URL
    GITHUB_TOKEN       — GitHub PAT with `repo` scope
    GITHUB_REPOSITORY  — "owner/repo" (auto-set in GitHub Actions)
"""

import asyncio
import os
import sys

# Add src/ to path so we can import bot.backup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bot.backup.github_storage import GitHubReleaseStorage
from bot.backup.service import create_backup


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not github_token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    github_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not github_repo or "/" not in github_repo:
        print(
            "ERROR: GITHUB_REPOSITORY must be set to 'owner/repo'.",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo = github_repo.split("/", 1)

    # Normalise Railway's postgresql:// to postgresql+asyncpg:// for service
    if database_url.startswith("postgresql://"):
        database_url_async = database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    else:
        database_url_async = database_url

    print("Creating database backup...")
    filename, data = await create_backup(database_url_async)
    print(f"Backup created: {filename} ({len(data)} bytes)")

    print("Uploading to GitHub Releases...")
    storage = GitHubReleaseStorage(token=github_token, owner=owner, repo=repo)
    url = await storage.upload(filename, data)
    print(f"Backup uploaded: {url}")


if __name__ == "__main__":
    asyncio.run(main())

