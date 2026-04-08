"""Integration tests for tests/seed.py."""

import csv
import sys
from pathlib import Path

from sqlalchemy import select

from bot.db import Character

# Ensure tests/ is on sys.path so seed can be imported directly.
sys.path.insert(0, str(Path(__file__).parent))
import seed as seed_module  # noqa: E402


def _count_csv_rows() -> int:
    """Return the number of data rows in the active seed CSV file."""
    with seed_module._CSV_PATH.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


class TestSeedDb:
    async def test_inserts_all_csv_rows(self, session_factory) -> None:
        """seed_db must insert one character per row in seed_data.csv."""
        expected = _count_csv_rows()
        await seed_module.seed_db(session_factory)

        async with session_factory() as session:
            result = await session.execute(select(Character))
            characters = result.scalars().all()

        assert len(characters) == expected

    async def test_characters_have_correct_owner_ids(
        self, session_factory
    ) -> None:
        """Characters must be owned by the owner_id values in seed_data.csv."""
        await seed_module.seed_db(session_factory)

        async with session_factory() as session:
            result = await session.execute(select(Character))
            characters = result.scalars().all()

        owner_ids = {c.owner_id for c in characters}
        assert "111111111111111111" in owner_ids
        assert "222222222222222222" in owner_ids

    async def test_idempotent_second_call(self, session_factory) -> None:
        """Running seed_db twice must not raise and must not duplicate rows."""
        expected = _count_csv_rows()
        await seed_module.seed_db(session_factory)
        await seed_module.seed_db(session_factory)  # must not raise

        async with session_factory() as session:
            result = await session.execute(select(Character))
            characters = result.scalars().all()

        assert len(characters) == expected  # no duplicates

    async def test_missing_optional_columns_use_defaults(
        self, session_factory, tmp_path, monkeypatch
    ) -> None:
        """A CSV row with only required columns uses /character create defaults."""
        # Write a minimal CSV with only required columns.
        minimal_csv = tmp_path / "minimal.csv"
        minimal_csv.write_text(
            "owner_id,name,char_class,race,background,alignment\n"
            "333333333333333333,Bilbo,Rogue,Hobbit,Criminal,Neutral Good\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(seed_module, "_CSV_PATH", minimal_csv)

        await seed_module.seed_db(session_factory)

        async with session_factory() as session:
            result = await session.execute(
                select(Character).where(Character.name == "Bilbo")
            )
            bilbo = result.scalar_one()

        assert bilbo.level == 1
        assert bilbo.strength == 10
        assert bilbo.experience_points == 0

    async def test_two_owners_have_distinct_characters(
        self, session_factory
    ) -> None:
        """Characters from different owners must not be accessible cross-owner."""
        await seed_module.seed_db(session_factory)

        async with session_factory() as session:
            owner1 = await session.execute(
                select(Character).where(
                    Character.owner_id == "111111111111111111"
                )
            )
            owner2 = await session.execute(
                select(Character).where(
                    Character.owner_id == "222222222222222222"
                )
            )

        owner1_names = {c.name for c in owner1.scalars().all()}
        owner2_names = {c.name for c in owner2.scalars().all()}

        assert owner1_names == {"Thorin", "Gandalf"}
        assert owner2_names == {"Legolas"}
        assert owner1_names.isdisjoint(owner2_names)

