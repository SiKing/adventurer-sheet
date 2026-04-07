"""Entry point for the bot: python -m bot (run from src/)."""

import argparse
import asyncio
import importlib
import logging

import discord
from sqlalchemy.ext.asyncio import create_async_engine
from discord.ext import commands

from bot.config import load_config
from bot.db import create_tables, get_session_factory
from bot.repository import CharacterRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


async def main() -> None:
    """Create the bot, load cogs, and start the connection."""
    parser = argparse.ArgumentParser(description="Adventurer Sheet bot")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed the database with test data before starting (local dev only).",
    )
    args = parser.parse_args()

    config = load_config()
    database_url = config["DATABASE_URL"]
    logger.info("Database: %s", database_url)

    # Set up the async database engine and create tables
    engine = create_async_engine(database_url, echo=False)
    await create_tables(engine)
    session_factory = get_session_factory(engine)

    # Optionally seed test data (local dev only — tests/seed.py is never in the Docker image)
    if args.seed:
        try:
            seed_module = importlib.import_module("seed")
            await seed_module.seed_db(session_factory)
            logger.info("Seed data loaded.")
        except ModuleNotFoundError:
            logger.warning(
                "--seed flag was passed but tests/seed.py was not found. "
                "Skipping seed. (This is expected in production.)"
            )

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix="!",  # fallback prefix — we use slash commands
        intents=intents,
        description="Adventurer Sheet — D&D 5e character sheet bot",
    )

    # Stash the repo on the bot so the character cog setup() can access it
    bot.__dict__["_character_repo"] = CharacterRepository(session_factory)

    @bot.event
    async def on_ready() -> None:
        logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
        logger.info("Syncing commands...")
        await bot.tree.sync()
        logger.info("Commands synced. Bot is ready.")

    # Load cogs
    await bot.load_extension("bot.cogs.hello")
    logger.info("Loaded cog: hello")
    await bot.load_extension("bot.cogs.about")
    logger.info("Loaded cog: about")
    await bot.load_extension("bot.cogs.character")
    logger.info("Loaded cog: character")

    # Connect to Discord
    await bot.start(config["DISCORD_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())

