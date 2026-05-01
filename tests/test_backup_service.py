"""Tests for bot.backup.service module."""

import gzip
from unittest.mock import AsyncMock, patch

import pytest

from bot.backup.service import _normalize_url, create_backup

_PATCH_TARGET = (
    "bot.backup.service.asyncio.create_subprocess_exec"
)


class TestNormalizeUrl:
    """Tests for the _normalize_url helper."""

    def test_converts_asyncpg_to_standard(self) -> None:
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        assert _normalize_url(url) == "postgresql://user:pass@host:5432/db"

    def test_leaves_standard_url_unchanged(self) -> None:
        url = "postgresql://user:pass@host:5432/db"
        assert _normalize_url(url) == url

    def test_leaves_other_schemes_unchanged(self) -> None:
        url = "sqlite:///test.db"
        assert _normalize_url(url) == url


class TestCreateBackup:
    """Tests for the create_backup function."""

    async def test_creates_compressed_backup(self) -> None:
        """Backup produces a valid gzipped SQL file."""
        fake_sql = b"DROP TABLE IF EXISTS characters;\n"

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (fake_sql, b"")
        mock_process.returncode = 0

        with patch(_PATCH_TARGET, return_value=mock_process):
            filename, data = await create_backup(
                "postgresql://x@localhost/db",
            )

        assert filename.startswith("backup-")
        assert filename.endswith(".sql.gz")
        decompressed = gzip.decompress(data)
        assert decompressed == fake_sql

    async def test_backup_filename_has_timestamp(self) -> None:
        """Filename contains a UTC timestamp."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"SQL", b"")
        mock_process.returncode = 0

        with patch(_PATCH_TARGET, return_value=mock_process):
            filename, _ = await create_backup(
                "postgresql://x@localhost/db",
            )

        stem = filename.removesuffix(".sql.gz")
        parts = stem.split("-")
        assert len(parts) >= 4  # backup, YYYY, MM, DDT...

    async def test_backup_fails_with_nonzero_exit(self) -> None:
        """pg_dump failure raises RuntimeError."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"refused")
        mock_process.returncode = 1

        with (
            patch(_PATCH_TARGET, return_value=mock_process),
            pytest.raises(RuntimeError, match="pg_dump failed"),
        ):
            await create_backup(
                "postgresql://bad@localhost/nonexistent",
            )
