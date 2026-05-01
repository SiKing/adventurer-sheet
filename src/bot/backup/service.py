"""Backup service — orchestrates pg_dump and storage upload/download.

This module is storage-agnostic: it accepts any BackupStorage implementation.
"""

import asyncio
import gzip
import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


async def create_backup(database_url: str) -> tuple[str, bytes]:
    """Run pg_dump and return (filename, compressed_data).

    Args:
        database_url: PostgreSQL connection URL (postgresql://... or
            postgresql+asyncpg://...).

    Returns:
        A tuple of (filename, gzipped SQL dump bytes).

    Raises:
        RuntimeError: If pg_dump fails.
    """
    # pg_dump needs a standard postgresql:// URL, not postgresql+asyncpg://
    pg_url = _normalize_url(database_url)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"backup-{timestamp}.sql.gz"

    logger.info("Running pg_dump...")
    process = await asyncio.create_subprocess_exec(
        "pg_dump",
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists",
        pg_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"pg_dump failed (exit {process.returncode}): {error_msg}")

    compressed = gzip.compress(stdout)
    logger.info(
        "Backup created: %s (%d bytes raw, %d bytes compressed)",
        filename,
        len(stdout),
        len(compressed),
    )
    return filename, compressed


def _normalize_url(database_url: str) -> str:
    """Convert a SQLAlchemy async URL to a standard PostgreSQL URL.

    "postgresql+asyncpg://..." → "postgresql://..."
    """
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return database_url

