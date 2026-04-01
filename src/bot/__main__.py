"""Entry point for the bot: python -m bot (run from src/)."""

import asyncio
import logging

import discord
from discord.ext import commands

from bot.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


async def main() -> None:
    """Create the bot, load cogs, and start the connection."""
    config = load_config()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix="!",  # fallback prefix — we use slash commands
        intents=intents,
        description="Adventurer Sheet — D&D 5e character sheet bot",
    )

    @bot.event
    async def on_ready() -> None:
        logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
        logger.info("Syncing commands...")
        await bot.tree.sync()
        logger.info("Commands synced. Bot is ready.")

    # Load cogs
    await bot.load_extension("bot.cogs.hello")
    logger.info("Loaded cog: hello")

    # Connect to Discord
    await bot.start(config["DISCORD_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())

