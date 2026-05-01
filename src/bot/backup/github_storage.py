"""GitHub Releases backup storage adapter.

Uploads and downloads database backups as GitHub Release assets.
Each backup creates a new release with a timestamped tag.
"""

import logging

import aiohttp

logger = logging.getLogger(__name__)

# GitHub API base URL (can be overridden for testing)
GITHUB_API = "https://api.github.com"
GITHUB_UPLOADS = "https://uploads.github.com"


class GitHubReleaseStorage:
    """Store backups as GitHub Release assets."""

    def __init__(self, token: str, owner: str, repo: str) -> None:
        """Initialise with GitHub credentials and repo info.

        Args:
            token: GitHub personal access token with `repo` scope.
            owner: Repository owner (e.g. "SiKing").
            repo: Repository name (e.g. "adventurer-sheet").
        """
        self._token = token
        self._owner = owner
        self._repo = repo
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @property
    def _api_base(self) -> str:
        return f"{GITHUB_API}/repos/{self._owner}/{self._repo}"

    async def upload(self, filename: str, data: bytes) -> str:
        """Create a GitHub Release and upload the backup as an asset.

        The release tag is derived from the filename (e.g. "backup-2026-05-01"
        from "backup-2026-05-01.sql.gz").

        Returns:
            The browser download URL for the uploaded asset.
        """
        # Derive tag from filename: "backup-2026-05-01.sql.gz" → "backup/2026-05-01"
        tag = _filename_to_tag(filename)

        async with aiohttp.ClientSession(headers=self._headers) as session:
            # Create the release
            release_url = f"{self._api_base}/releases"
            release_payload = {
                "tag_name": tag,
                "name": f"Database Backup — {tag}",
                "body": f"Automated database backup: `{filename}`",
                "draft": False,
                "prerelease": True,  # Don't pollute "latest"
            }
            async with session.post(release_url, json=release_payload) as resp:
                if resp.status != 201:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Failed to create release (HTTP {resp.status}): {body}"
                    )
                release = await resp.json()
                release_id = release["id"]
                logger.info("Created release %s (id=%d)", tag, release_id)

            # Upload the asset
            upload_url = (
                f"{GITHUB_UPLOADS}/repos/{self._owner}/{self._repo}"
                f"/releases/{release_id}/assets?name={filename}"
            )
            upload_headers = {
                **self._headers,
                "Content-Type": "application/gzip",
            }
            async with session.post(
                upload_url, data=data, headers=upload_headers
            ) as resp:
                if resp.status != 201:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Failed to upload asset (HTTP {resp.status}): {body}"
                    )
                asset = await resp.json()
                download_url = asset["browser_download_url"]
                logger.info("Uploaded %s → %s", filename, download_url)
                return download_url

    async def download(self, filename: str) -> bytes:
        """Download a backup asset from the corresponding release.

        Raises:
            FileNotFoundError: If no release/asset matches the filename.
        """
        tag = _filename_to_tag(filename)

        async with aiohttp.ClientSession(headers=self._headers) as session:
            # Get release by tag
            release_url = f"{self._api_base}/releases/tags/{tag}"
            async with session.get(release_url) as resp:
                if resp.status == 404:
                    raise FileNotFoundError(
                        f"No release found for tag '{tag}'"
                    )
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Failed to get release (HTTP {resp.status}): {body}"
                    )
                release = await resp.json()

            # Find the asset
            assets = release.get("assets", [])
            asset = next((a for a in assets if a["name"] == filename), None)
            if asset is None:
                raise FileNotFoundError(
                    f"Asset '{filename}' not found in release '{tag}'"
                )

            # Download the asset
            asset_url = asset["url"]
            dl_headers = {
                **self._headers,
                "Accept": "application/octet-stream",
            }
            async with session.get(asset_url, headers=dl_headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Failed to download asset (HTTP {resp.status}): {body}"
                    )
                return await resp.read()

    async def list_backups(self) -> list[str]:
        """List backup filenames from all pre-release releases, newest first."""
        filenames: list[str] = []

        async with aiohttp.ClientSession(headers=self._headers) as session:
            releases_url = f"{self._api_base}/releases?per_page=100"
            async with session.get(releases_url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"Failed to list releases (HTTP {resp.status}): {body}"
                    )
                releases = await resp.json()

            for release in releases:
                if not release.get("prerelease"):
                    continue
                for asset in release.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(".sql.gz"):
                        filenames.append(name)

        return filenames


def _filename_to_tag(filename: str) -> str:
    """Convert a backup filename to a release tag.

    "backup-2026-05-01T12-00-00.sql.gz" → "backup/2026-05-01T12-00-00"
    """
    # Strip .sql.gz suffix
    stem = filename.removesuffix(".sql.gz").removesuffix(".sql")
    # Replace first hyphen after "backup" with a slash for tag namespacing
    if stem.startswith("backup-"):
        stem = "backup/" + stem[7:]
    return stem

