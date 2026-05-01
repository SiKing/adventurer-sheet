"""Shared async pytest fixtures for database integration tests."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from bot.db import Base, Character, create_tables, get_session_factory

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://bot:bot@localhost:5432/adventurer_sheet",
)


@pytest.fixture()
async def engine() -> AsyncEngine:
    """PostgreSQL engine, tables dropped and recreated fresh for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await create_tables(engine)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def session_factory(engine: AsyncEngine):
    """Async session factory bound to the in-memory engine."""
    factory = get_session_factory(engine)
    yield factory


@pytest.fixture()
async def sample_character(session_factory) -> Character:
    """Insert and return a single Character for tests that need an existing row."""
    from bot.repository import CharacterRepository

    repo = CharacterRepository(session_factory)
    return await repo.create(
        owner_id="111111111111111111",
        name="Thorin",
        char_class="Fighter",
        level=5,
        race="Dwarf",
        background="Soldier",
        alignment="Lawful Good",
    )

