"""Tests for bot.config module."""

from pathlib import Path

import pytest

from bot.config import load_config


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_returns_token_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config loads successfully when DISCORD_TOKEN is set."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token-12345")
        config = load_config()
        assert config["DISCORD_TOKEN"] == "test-token-12345"

    def test_load_config_raises_when_token_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Config raises RuntimeError when DISCORD_TOKEN is not set."""
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
        # Prevent load_dotenv from reading the real .env file
        monkeypatch.setattr("bot.config.load_dotenv", lambda *a, **kw: None)
        with pytest.raises(RuntimeError, match="DISCORD_TOKEN is not set"):
            load_config()

    def test_load_config_raises_when_token_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config raises RuntimeError when DISCORD_TOKEN is empty."""
        monkeypatch.setenv("DISCORD_TOKEN", "   ")
        with pytest.raises(RuntimeError, match="DISCORD_TOKEN is not set"):
            load_config()

    def test_load_config_strips_whitespace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config strips leading/trailing whitespace from token."""
        monkeypatch.setenv("DISCORD_TOKEN", "  my-token  ")
        config = load_config()
        assert config["DISCORD_TOKEN"] == "my-token"

    def test_load_config_returns_database_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config returns DATABASE_URL in the config dict."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        config = load_config()
        assert config["DATABASE_URL"] == "sqlite+aiosqlite:///./test.db"

    def test_load_config_database_url_has_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config falls back to the default DATABASE_URL when env var is absent."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        config = load_config()
        assert "DATABASE_URL" in config
        assert "sqlite+aiosqlite" in config["DATABASE_URL"]

    def test_load_config_returns_dev_guild_id_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config returns DEV_GUILD_ID when the env var is set."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        monkeypatch.setenv("DEV_GUILD_ID", "123456789012345678")
        config = load_config()
        assert config["DEV_GUILD_ID"] == "123456789012345678"

    def test_load_config_dev_guild_id_empty_when_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config returns an empty string for DEV_GUILD_ID when env var is absent."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        monkeypatch.delenv("DEV_GUILD_ID", raising=False)
        # Prevent load_dotenv from re-reading the real .env, which may set DEV_GUILD_ID.
        monkeypatch.setattr("bot.config.load_dotenv", lambda *a, **kw: None)
        config = load_config()
        assert config["DEV_GUILD_ID"] == ""

