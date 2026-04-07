"""Shared async pytest fixtures for database integration tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from bot.db import Character, create_tables, get_session_factory


@pytest.fixture()
async def engine() -> AsyncEngine:
    """In-memory async SQLite engine, tables created fresh for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
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

