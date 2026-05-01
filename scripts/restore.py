#!/usr/bin/env python3
"""Download a backup from GitHub Releases and restore it to PostgreSQL.

Usage (from project root):
    python scripts/restore.py                      # lists available backups
    python scripts/restore.py <filename>           # restores the named backup

Required environment variables:
    DATABASE_URL       — PostgreSQL connection URL
    GITHUB_TOKEN       — GitHub PAT with `repo` scope
    GITHUB_REPOSITORY  — "owner/repo" (auto-set in GitHub Actions)
"""

import asyncio
import gzip
import os
import sys

# Add src/ to path so we can import bot.backup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bot.backup.github_storage import GitHubReleaseStorage


async def main() -> None:
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not github_token:
        print("ERROR: GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    github_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not github_repo or "/" not in github_repo:
        print(
            "ERROR: GITHUB_REPOSITORY must be 'owner/repo'.",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo = github_repo.split("/", 1)
    storage = GitHubReleaseStorage(
        token=github_token, owner=owner, repo=repo,
    )

    # No filename arg → list backups
    if len(sys.argv) < 2:
        print("Available backups:")
        backups = await storage.list_backups()
        if not backups:
            print("  (none)")
        for name in backups:
            print(f"  {name}")
        print(
            "\nUsage: python scripts/restore.py <filename>",
        )
        return

    filename = sys.argv[1]

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    # Normalise to standard postgresql:// for psql
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace(
            "postgresql+asyncpg://", "postgresql://", 1,
        )

    print(f"Downloading {filename}...")
    data = await storage.download(filename)
    print(f"Downloaded {len(data)} bytes.")

    # Decompress
    sql = gzip.decompress(data)
    print(f"Decompressed to {len(sql)} bytes.")

    # Restore via psql
    print("Restoring to database...")
    process = await asyncio.create_subprocess_exec(
        "psql", database_url,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=sql)

    if process.returncode != 0:
        print(
            f"psql failed (exit {process.returncode}):",
            file=sys.stderr,
        )
        print(stderr.decode(), file=sys.stderr)
        sys.exit(1)

    print("Restore complete.")


if __name__ == "__main__":
    asyncio.run(main())

