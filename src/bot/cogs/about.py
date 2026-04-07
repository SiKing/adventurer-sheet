"""About cog — provides the /about slash command."""

import tomllib
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


def get_project_info() -> dict[str, str]:
    """Read project metadata from pyproject.toml.

    Returns:
        A dict with 'version' and 'description' keys.
        Values fall back to "unknown" if the file or key is missing.
    """
    toml_path = Path(__file__).resolve().parent.parent.parent.parent / "pyproject.toml"
    try:
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        project = data["project"]
        return {
            "version": project.get("version", "unknown"),
            "description": project.get("description", "unknown"),
        }
    except (FileNotFoundError, KeyError, OSError):
        return {"version": "unknown", "description": "unknown"}


class About(commands.Cog):
    """Provides general information about the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="about", description="Show information about this bot.")
    async def about(self, interaction: discord.Interaction) -> None:
        """Display bot information including current version and description."""
        info = get_project_info()
        embed = discord.Embed(
            title="Adventurer Sheet",
            description=info["description"],
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="Version", value=info["version"], inline=True)
        embed.set_footer(text="Made with discord.py")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Register the About cog with the bot."""
    await bot.add_cog(About(bot))

