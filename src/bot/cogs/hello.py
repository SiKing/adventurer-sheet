"""Hello cog — provides the /hello slash command."""

import discord
from discord import app_commands
from discord.ext import commands


class Hello(commands.Cog):
    """A simple greeting cog to verify the bot is working."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello to the bot!")
    async def hello(self, interaction: discord.Interaction) -> None:
        """Respond with a friendly greeting."""
        await interaction.response.send_message("Hello, World! 🎲")


async def setup(bot: commands.Bot) -> None:
    """Register the Hello cog with the bot."""
    await bot.add_cog(Hello(bot))

