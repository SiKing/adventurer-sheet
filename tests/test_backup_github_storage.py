"""Tests for bot.backup.github_storage module."""

from bot.backup.github_storage import _filename_to_tag


class TestFilenameToTag:
    """Tests for the _filename_to_tag helper."""

    def test_standard_filename(self) -> None:
        assert _filename_to_tag("backup-2026-05-01T12-00-00.sql.gz") == (
            "backup/2026-05-01T12-00-00"
        )

    def test_date_only_filename(self) -> None:
        assert _filename_to_tag("backup-2026-05-01.sql.gz") == "backup/2026-05-01"

    def test_sql_only_suffix(self) -> None:
        assert _filename_to_tag("backup-2026-05-01.sql") == "backup/2026-05-01"

    def test_no_backup_prefix(self) -> None:
        """Filenames without 'backup-' prefix are returned as-is (minus suffix)."""
        assert _filename_to_tag("dump-2026-05-01.sql.gz") == "dump-2026-05-01"
