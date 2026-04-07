"""Tests for the about cog."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.cogs.about import About, get_project_info


class TestGetProjectInfo:
    """Tests for the get_project_info helper."""

    def test_returns_version_and_description(self) -> None:
        """get_project_info returns version and description from pyproject.toml."""
        info = get_project_info()
        assert info["version"] != "unknown"
        assert len(info["version"]) > 0
        parts = info["version"].split(".")
        assert len(parts) == 3  # major.minor.patch
        assert info["description"] != "unknown"
        assert len(info["description"]) > 0

    def test_returns_unknown_when_file_missing(self) -> None:
        """get_project_info returns 'unknown' when pyproject.toml cannot be found."""
        with patch("pathlib.Path.open", side_effect=FileNotFoundError):
            info = get_project_info()
        assert info["version"] == "unknown"
        assert info["description"] == "unknown"

    def test_returns_unknown_on_missing_key(self) -> None:
        """get_project_info returns 'unknown' values when project keys are absent."""
        with (
            patch("bot.cogs.about.tomllib.load", return_value={}),
            patch("builtins.open", MagicMock()),
        ):
            info = get_project_info()
        assert info["version"] == "unknown"
        assert info["description"] == "unknown"


class TestAboutCog:
    """Tests for the About cog."""

    @pytest.fixture()
    def bot(self) -> MagicMock:
        """Create a mock bot instance."""
        return MagicMock()

    @pytest.fixture()
    def cog(self, bot: MagicMock) -> About:
        """Create an About cog instance."""
        return About(bot)

    @pytest.mark.asyncio
    async def test_about_command_sends_embed(self, cog: About) -> None:
        """The /about command sends an embed."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        mock_info = {"version": "1.2.3", "description": "A test bot."}
        with patch("bot.cogs.about.get_project_info", return_value=mock_info):
            await cog.about.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs.get("embed") or call_kwargs.args[0]
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Adventurer Sheet"

    @pytest.mark.asyncio
    async def test_about_command_embed_contains_version(self, cog: About) -> None:
        """The /about embed field shows the version from get_project_info."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        mock_info = {"version": "0.1.1", "description": "A test bot."}
        with patch("bot.cogs.about.get_project_info", return_value=mock_info):
            await cog.about.callback(cog, interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs.get("embed") or call_kwargs.args[0]
        version_field = next(f for f in embed.fields if f.name == "Version")
        assert version_field.value == "0.1.1"

    @pytest.mark.asyncio
    async def test_about_command_embed_contains_description(self, cog: About) -> None:
        """The /about embed description comes from pyproject.toml."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        mock_info = {"version": "0.1.1", "description": "A D&D 5e character sheet bot."}
        with patch("bot.cogs.about.get_project_info", return_value=mock_info):
            await cog.about.callback(cog, interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs.get("embed") or call_kwargs.args[0]
        assert embed.description == "A D&D 5e character sheet bot."

