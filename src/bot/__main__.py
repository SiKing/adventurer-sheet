"""Entry point for the bot: python -m bot (run from src/)."""

import argparse
import asyncio
import importlib.util
import logging
from pathlib import Path

import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import create_async_engine

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
    parser.add_argument(
        "--dev-guild",
        metavar="GUILD_ID",
        default=None,
        help=(
            "Sync slash commands to this guild ID instantly instead of globally. "
            "Use during local development to avoid the ~1-hour global sync delay. "
            "Can also be set via the DEV_GUILD_ID environment variable."
        ),
    )
    args = parser.parse_args()

    config = load_config()
    database_url = config["DATABASE_URL"]
    logger.info("Database: %s", database_url)

    # Resolve the dev guild ID: CLI flag takes priority, then env var.
    dev_guild_id: int | None = None
    raw_guild = args.dev_guild or config.get("DEV_GUILD_ID")
    if raw_guild:
        try:
            dev_guild_id = int(raw_guild)
        except ValueError:
            logger.warning(
                "Invalid DEV_GUILD_ID %r — must be an integer. "
                "Falling back to global sync.",
                raw_guild,
            )

    # Set up the async database engine and create tables
    engine = create_async_engine(database_url, echo=False)
    await create_tables(engine)
    session_factory = get_session_factory(engine)

    # Optionally seed test data (local dev only)
    # tests/seed.py is never copied into the Docker image
    if args.seed:
        # Resolve tests/seed.py relative to the project root
        # (two levels up from src/bot/__main__.py).
        project_root = Path(__file__).resolve().parent.parent.parent
        seed_path = project_root / "tests" / "seed.py"
        if seed_path.exists():
            spec = importlib.util.spec_from_file_location("seed", seed_path)
            if spec is None or spec.loader is None:
                logger.warning("Could not load seed module from %s.", seed_path)
            else:
                seed_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(seed_module)
                await seed_module.seed_db(session_factory)
                logger.info("Seed data loaded.")
        else:
            logger.warning(
                "--seed flag was passed but %s was not found. "
                "Skipping seed. (This is expected in production.)",
                seed_path,
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
        if dev_guild_id is not None:
            guild = discord.Object(id=dev_guild_id)
            # Guild sync: push the full command tree to this guild (instant).
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            logger.info(
                "Commands synced to dev guild %d (instant). Bot is ready.",
                dev_guild_id,
            )
        else:
            logger.info("Syncing commands globally (may take up to 1 hour)...")
            await bot.tree.sync()
            logger.info("Global sync complete. Bot is ready.")

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

