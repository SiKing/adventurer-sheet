"""Database engine, ORM model, and session factory for Adventurer Sheet."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class Character(Base):
    """ORM model for the 'characters' table."""

    __tablename__ = "characters"

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_owner_name"),
        Index("ix_characters_owner_id", "owner_id"),
    )

    # --- Identity ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    char_class: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    race: Mapped[str] = mapped_column(String(50), nullable=False)
    background: Mapped[str] = mapped_column(String(50), nullable=False)
    alignment: Mapped[str] = mapped_column(String(20), nullable=False)

    # --- Ability scores ---
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    constitution: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    wisdom: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # --- Combat stats ---
    armor_class: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    speed: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # --- Derived stats (stored; player-overridable) ---
    initiative: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proficiency_bonus: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    passive_perception: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # --- Progression ---
    experience_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Audit timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Character id={self.id} owner={self.owner_id!r} name={self.name!r}>"
        )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return an async session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(engine: AsyncEngine) -> None:
    """Create all tables defined in Base.metadata (no-op if they already exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

