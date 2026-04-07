"""Seed the local development database from tests/seed_data.csv.

This module is intentionally placed under tests/ so it is never copied into
the Docker image (Dockerfile only copies src/). It is imported dynamically
by __main__.py only when the --seed flag is passed.
"""

import csv
import logging
from pathlib import Path

from bot.repository import CharacterRepository

from bot.errors import CharacterAlreadyExistsError

logger = logging.getLogger(__name__)

# Absolute path to the CSV file, resolved relative to this file's location.
_CSV_PATH = Path(__file__).parent / "seed_data.csv"

# Column defaults matching /character create behaviour.
_DEFAULTS: dict[str, int | str] = {
    "level": 1,
    "strength": 10,
    "dexterity": 10,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 10,
    "charisma": 10,
    "armor_class": 10,
    "speed": 30,
    "max_hp": 1,
    "current_hp": 1,
    "initiative": 0,
    "proficiency_bonus": 2,
    "passive_perception": 10,
    "experience_points": 0,
}

# Integer columns that need type conversion from CSV strings.
_INT_COLUMNS = {
    "level",
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
    "armor_class",
    "speed",
    "max_hp",
    "current_hp",
    "initiative",
    "proficiency_bonus",
    "passive_perception",
    "experience_points",
}


async def seed_db(session_factory) -> None:
    """Read seed_data.csv and insert each row into the database.

    Rows whose (owner_id, name) already exist are skipped silently.
    """
    repo = CharacterRepository(session_factory)

    with _CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Apply defaults for missing or empty fields.
            for col, default in _DEFAULTS.items():
                if not row.get(col):
                    row[col] = default

            # Convert integer columns.
            for col in _INT_COLUMNS:
                if col in row:
                    row[col] = int(row[col])

            try:
                await repo.create(
                    owner_id=row["owner_id"],
                    name=row["name"],
                    char_class=row["char_class"],
                    level=int(row["level"]),
                    race=row["race"],
                    background=row["background"],
                    alignment=row["alignment"],
                    strength=int(row["strength"]),
                    dexterity=int(row["dexterity"]),
                    constitution=int(row["constitution"]),
                    intelligence=int(row["intelligence"]),
                    wisdom=int(row["wisdom"]),
                    charisma=int(row["charisma"]),
                    armor_class=int(row["armor_class"]),
                    speed=int(row["speed"]),
                    max_hp=int(row["max_hp"]),
                    current_hp=int(row["current_hp"]),
                    initiative=int(row["initiative"]),
                    proficiency_bonus=int(row["proficiency_bonus"]),
                    passive_perception=int(row["passive_perception"]),
                    experience_points=int(row["experience_points"]),
                )
                logger.info(
                    "Seeded character: %s (owner %s)", row["name"], row["owner_id"]
                )
            except CharacterAlreadyExistsError:
                logger.info(
                    "Skipped existing character: %s (owner %s)",
                    row["name"],
                    row["owner_id"],
                )

