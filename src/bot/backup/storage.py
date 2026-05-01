"""Protocol for backup storage backends.

Any new storage backend (S3, R2, B2, etc.) only needs to implement this
protocol — no other code changes required.
"""

from typing import Protocol


class BackupStorage(Protocol):
    """Interface for backup file storage."""

    async def upload(self, filename: str, data: bytes) -> str:
        """Upload backup data.

        Args:
            filename: Name for the backup file (e.g. "backup-2026-05-01.sql.gz").
            data: Compressed SQL dump bytes.

        Returns:
            A URL or identifier for the uploaded backup.
        """
        ...

    async def download(self, filename: str) -> bytes:
        """Download backup data by filename.

        Args:
            filename: The backup filename to retrieve.

        Returns:
            The raw backup file bytes.

        Raises:
            FileNotFoundError: If the backup does not exist.
        """
        ...

    async def list_backups(self) -> list[str]:
        """List available backup filenames, newest first.

        Returns:
            A list of backup filenames.
        """
        ...

