"""Tests for the hello cog."""

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.cogs.hello import Hello


class TestHelloCog:
    """Tests for the Hello cog."""

    @pytest.fixture()
    def bot(self) -> MagicMock:
        """Create a mock bot instance."""
        return MagicMock()

    @pytest.fixture()
    def cog(self, bot: MagicMock) -> Hello:
        """Create a Hello cog instance."""
        return Hello(bot)

    @pytest.mark.asyncio
    async def test_hello_command_responds(self, cog: Hello) -> None:
        """The /hello command sends the expected greeting."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        await cog.hello.callback(cog, interaction)
        interaction.response.send_message.assert_called_once_with(
            "Hello, World! 🎲"
        )

