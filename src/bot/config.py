"""Bot configuration — loads and validates environment variables."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_config() -> dict[str, str]:
    """Load configuration from .env file and environment variables.

    Returns:
        A dict with validated configuration values.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    # Load .env from project root (two levels up from src/bot/)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. "
            "Copy .env.example to .env and add your bot token."
        )

    logger.info("Configuration loaded successfully.")
    return {"DISCORD_TOKEN": token}

