"""Integration tests for src/bot/db.py — ORM model and engine setup."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.db import Character, create_tables, get_session_factory


class TestCreateTables:
    async def test_creates_characters_table(self, engine: AsyncEngine) -> None:
        """create_tables must create the 'characters' table."""

        def _check(conn):
            inspector = inspect(conn)
            return "characters" in inspector.get_table_names()

        async with engine.connect() as conn:
            result = await conn.run_sync(_check)
        assert result is True

    async def test_idempotent_second_call(self, engine: AsyncEngine) -> None:
        """Calling create_tables twice must not raise."""
        await create_tables(engine)  # second call


class TestCharacterModel:
    async def test_insert_and_retrieve_all_columns(
        self, session_factory
    ) -> None:
        """A Character row can be inserted with all fields and retrieved."""
        async with session_factory() as session:
            char = Character(
                owner_id="111111111111111111",
                name="Thorin",
                char_class="Fighter",
                level=5,
                race="Dwarf",
                background="Soldier",
                alignment="Lawful Good",
                strength=18,
                dexterity=10,
                constitution=16,
                intelligence=10,
                wisdom=12,
                charisma=8,
                armor_class=16,
                speed=25,
                max_hp=52,
                current_hp=52,
                initiative=0,
                proficiency_bonus=3,
                passive_perception=11,
                experience_points=6500,
            )
            session.add(char)
            await session.commit()
            await session.refresh(char)

        assert char.id is not None
        assert char.name == "Thorin"
        assert char.level == 5
        assert char.experience_points == 6500

    async def test_experience_points_defaults_to_zero(
        self, session_factory
    ) -> None:
        """experience_points must default to 0 when omitted."""
        async with session_factory() as session:
            char = Character(
                owner_id="111111111111111111",
                name="Gimli",
                char_class="Fighter",
                level=1,
                race="Dwarf",
                background="Soldier",
                alignment="Lawful Good",
            )
            session.add(char)
            await session.commit()
            await session.refresh(char)

        assert char.experience_points == 0

    async def test_integer_columns_default_correctly(
        self, session_factory
    ) -> None:
        """Stat columns must use their plan-specified defaults when omitted."""
        async with session_factory() as session:
            char = Character(
                owner_id="111111111111111111",
                name="Legolas",
                char_class="Ranger",
                level=1,
                race="Elf",
                background="Outlander",
                alignment="Chaotic Good",
            )
            session.add(char)
            await session.commit()
            await session.refresh(char)

        assert char.strength == 10
        assert char.dexterity == 10
        assert char.constitution == 10
        assert char.intelligence == 10
        assert char.wisdom == 10
        assert char.charisma == 10
        assert char.armor_class == 10
        assert char.speed == 30
        assert char.max_hp == 1
        assert char.current_hp == 1
        assert char.initiative == 0
        assert char.proficiency_bonus == 2
        assert char.passive_perception == 10

    async def test_timestamps_set_on_insert(self, session_factory) -> None:
        """created_at and updated_at must be populated after insert."""
        async with session_factory() as session:
            char = Character(
                owner_id="111111111111111111",
                name="Gandalf",
                char_class="Wizard",
                level=10,
                race="Human",
                background="Sage",
                alignment="Neutral Good",
            )
            session.add(char)
            await session.commit()
            await session.refresh(char)

        assert char.created_at is not None
        assert char.updated_at is not None

    async def test_updated_at_changes_after_update(
        self, session_factory
    ) -> None:
        """updated_at must change after an UPDATE; created_at must not."""
        from sqlalchemy import select

        async with session_factory() as session:
            char = Character(
                owner_id="111111111111111111",
                name="Aragorn",
                char_class="Ranger",
                level=1,
                race="Human",
                background="Outlander",
                alignment="Neutral Good",
            )
            session.add(char)
            await session.commit()
            await session.refresh(char)
            created_at_before = char.created_at
            updated_at_before = char.updated_at

        # Perform an update in a new session
        async with session_factory() as session:
            result = await session.execute(
                select(Character).where(Character.name == "Aragorn")
            )
            char = result.scalar_one()
            char.level = 2
            await session.commit()
            await session.refresh(char)

        assert char.created_at == created_at_before
        assert char.updated_at >= updated_at_before

    async def test_unique_constraint_owner_name(self, session_factory) -> None:
        """Inserting two characters with the same (owner_id, name) must raise IntegrityError."""  # noqa: E501
        async with session_factory() as session:
            char1 = Character(
                owner_id="111111111111111111",
                name="Thorin",
                char_class="Fighter",
                level=1,
                race="Dwarf",
                background="Soldier",
                alignment="Lawful Good",
            )
            session.add(char1)
            await session.commit()

        with pytest.raises(IntegrityError):
            async with session_factory() as session:
                char2 = Character(
                    owner_id="111111111111111111",
                    name="Thorin",
                    char_class="Wizard",
                    level=1,
                    race="Dwarf",
                    background="Sage",
                    alignment="Neutral Good",
                )
                session.add(char2)
                await session.commit()

    async def test_same_name_different_owner_is_allowed(
        self, session_factory
    ) -> None:
        """Two different owners may have a character with the same name."""
        async with session_factory() as session:
            for owner in ("111111111111111111", "222222222222222222"):
                char = Character(
                    owner_id=owner,
                    name="Thorin",
                    char_class="Fighter",
                    level=1,
                    race="Dwarf",
                    background="Soldier",
                    alignment="Lawful Good",
                )
                session.add(char)
            await session.commit()  # must not raise


class TestGetSessionFactory:
    def test_returns_callable(self, engine: AsyncEngine) -> None:
        """get_session_factory must return a callable session factory."""
        factory = get_session_factory(engine)
        assert callable(factory)

