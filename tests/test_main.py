"""Tests for the pure helper functions in src/bot/__main__.py."""

import logging
from pathlib import Path

import discord

from bot.__main__ import build_intents, resolve_dev_guild_id, resolve_seed_path

# ---------------------------------------------------------------------------
# resolve_dev_guild_id
# ---------------------------------------------------------------------------


class TestResolveDevGuildId:
    def test_valid_integer_string_returns_int(self) -> None:
        assert resolve_dev_guild_id("1317185696200396871") == 1317185696200396871

    def test_none_returns_none(self) -> None:
        assert resolve_dev_guild_id(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert resolve_dev_guild_id("") is None

    def test_non_integer_string_returns_none(self, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger="bot.__main__"):
            result = resolve_dev_guild_id("not-a-number")
        assert result is None

    def test_non_integer_string_logs_warning(self, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger="bot.__main__"):
            resolve_dev_guild_id("not-a-number")
        assert any("Invalid DEV_GUILD_ID" in r.message for r in caplog.records)

    def test_float_string_returns_none(self, caplog) -> None:
        # "1.5" is not a valid int
        with caplog.at_level(logging.WARNING, logger="bot.__main__"):
            result = resolve_dev_guild_id("1.5")
        assert result is None

    def test_zero_returns_zero(self) -> None:
        assert resolve_dev_guild_id("0") == 0


# ---------------------------------------------------------------------------
# resolve_seed_path
# ---------------------------------------------------------------------------


class TestResolveSeedPath:
    def test_returns_path_ending_with_tests_seed_py(self) -> None:
        from bot.__main__ import __file__ as main_file

        result = resolve_seed_path(Path(main_file))
        assert result.parts[-2:] == ("tests", "seed.py")

    def test_returns_absolute_path(self) -> None:
        from bot.__main__ import __file__ as main_file

        result = resolve_seed_path(Path(main_file))
        assert result.is_absolute()

    def test_points_to_existing_seed_file(self) -> None:
        """The resolved path should actually exist in this repo."""
        from bot.__main__ import __file__ as main_file

        result = resolve_seed_path(Path(main_file))
        assert result.exists(), f"Expected seed file at {result}"

    def test_custom_anchor_depth(self, tmp_path) -> None:
        # resolve_seed_path does:
        #   anchor.resolve().parent.parent.parent / "tests/seed.py"
        # The anchor must be exactly 3 levels deep under tmp_path so that
        # 3x .parent lands at tmp_path → tmp_path/tests/seed.py.
        # Mirror the real layout: tmp_path/src/bot/file.py
        fake_anchor = tmp_path / "src" / "bot" / "file.py"
        fake_anchor.parent.mkdir(parents=True)
        fake_anchor.touch()

        result = resolve_seed_path(fake_anchor)
        assert result == tmp_path / "tests" / "seed.py"


# ---------------------------------------------------------------------------
# build_intents
# ---------------------------------------------------------------------------


class TestBuildIntents:
    def test_returns_intents_instance(self) -> None:
        result = build_intents()
        assert isinstance(result, discord.Intents)

    def test_message_content_is_enabled(self) -> None:
        result = build_intents()
        assert result.message_content is True

