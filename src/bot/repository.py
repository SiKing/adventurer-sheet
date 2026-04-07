"""Character repository — all database access for the characters table."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.db import Character
from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
    InvalidFieldError,
    InvalidValueError,
)

# ---------------------------------------------------------------------------
# Field metadata
# ---------------------------------------------------------------------------

# Fields the player is allowed to edit via /character edit.
# All columns except id, owner_id, created_at, updated_at.
_EDITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "char_class",
        "level",
        "race",
        "background",
        "alignment",
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
)

# Integer fields — value must be a valid integer string.
_INTEGER_FIELDS: frozenset[str] = frozenset(
    {
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
)

# Integer fields that must be ≥ 1 (never zero or negative).
_POSITIVE_INT_FIELDS: frozenset[str] = frozenset(
    {
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
        "proficiency_bonus",
        "passive_perception",
    }
)


# ---------------------------------------------------------------------------
# Default-value helpers (used only at creation time)
# ---------------------------------------------------------------------------

def _ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _proficiency_bonus(level: int) -> int:
    return 2 + (level - 1) // 4


def _default_passive_perception(wisdom: int) -> int:
    return 10 + _ability_modifier(wisdom)


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class CharacterRepository:
    """Encapsulates all database access for the characters table."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    async def create(
        self,
        owner_id: str,
        name: str,
        char_class: str,
        race: str,
        background: str,
        alignment: str,
        level: int = 1,
        strength: int = 10,
        dexterity: int = 10,
        constitution: int = 10,
        intelligence: int = 10,
        wisdom: int = 10,
        charisma: int = 10,
        armor_class: int = 10,
        speed: int = 30,
        max_hp: int = 1,
        current_hp: int = 1,
        initiative: int | None = None,
        proficiency_bonus: int | None = None,
        passive_perception: int | None = None,
        experience_points: int = 0,
    ) -> Character:
        """Insert a new character row and return the hydrated ORM object.

        Raises:
            CharacterAlreadyExistsError: if (owner_id, name) already exists.
        """
        # Compute derived defaults from supplied stats if not overridden.
        if initiative is None:
            initiative = _ability_modifier(dexterity)
        if proficiency_bonus is None:
            proficiency_bonus = _proficiency_bonus(level)
        if passive_perception is None:
            passive_perception = _default_passive_perception(wisdom)

        char = Character(
            owner_id=owner_id,
            name=name,
            char_class=char_class,
            level=level,
            race=race,
            background=background,
            alignment=alignment,
            strength=strength,
            dexterity=dexterity,
            constitution=constitution,
            intelligence=intelligence,
            wisdom=wisdom,
            charisma=charisma,
            armor_class=armor_class,
            speed=speed,
            max_hp=max_hp,
            current_hp=current_hp,
            initiative=initiative,
            proficiency_bonus=proficiency_bonus,
            passive_perception=passive_perception,
            experience_points=experience_points,
        )

        async with self._session_factory() as session:
            try:
                session.add(char)
                await session.commit()
                await session.refresh(char)
            except IntegrityError as exc:
                await session.rollback()
                raise CharacterAlreadyExistsError(
                    f"Character '{name}' already exists for owner '{owner_id}'."
                ) from exc

        return char

    # ------------------------------------------------------------------
    # get_by_name
    # ------------------------------------------------------------------

    async def get_by_name(self, owner_id: str, name: str) -> Character:
        """Return the character matching (owner_id, name).

        Raises:
            CharacterNotFoundError: if no match is found.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(Character).where(
                    Character.owner_id == owner_id,
                    Character.name == name,
                )
            )
            char = result.scalar_one_or_none()

        if char is None:
            raise CharacterNotFoundError(
                f"Character '{name}' not found for owner '{owner_id}'."
            )
        return char

    # ------------------------------------------------------------------
    # list_by_owner
    # ------------------------------------------------------------------

    async def list_by_owner(self, owner_id: str) -> list[Character]:
        """Return all characters owned by owner_id, ordered by name ASC."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(Character)
                .where(Character.owner_id == owner_id)
                .order_by(Character.name)
            )
            return list(result.scalars().all())

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------

    async def update(
        self, owner_id: str, name: str, field: str, value: str
    ) -> Character:
        """Update a single editable field on a character and return the updated object.

        Raises:
            CharacterNotFoundError: if the character does not exist for this owner.
            InvalidFieldError: if field is not in the editable set.
            InvalidValueError: if value fails type or range validation.
        """
        if field not in _EDITABLE_FIELDS:
            raise InvalidFieldError(
                f"'{field}' is not an editable field. "
                f"Read-only fields: id, owner_id, created_at, updated_at."
            )

        # Validate and coerce value.
        coerced: str | int = value
        if field in _INTEGER_FIELDS:
            try:
                coerced = int(value)
            except (ValueError, TypeError) as exc:
                raise InvalidValueError(
                    f"'{field}' requires an integer value, got '{value}'."
                ) from exc
            if field in _POSITIVE_INT_FIELDS and coerced < 1:
                raise InvalidValueError(
                    f"'{field}' must be at least 1, got {coerced}."
                )

        async with self._session_factory() as session:
            result = await session.execute(
                select(Character).where(
                    Character.owner_id == owner_id,
                    Character.name == name,
                )
            )
            char = result.scalar_one_or_none()

            if char is None:
                raise CharacterNotFoundError(
                    f"Character '{name}' not found for owner '{owner_id}'."
                )

            setattr(char, field, coerced)
            await session.commit()
            await session.refresh(char)

        return char

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    async def delete(self, owner_id: str, name: str) -> None:
        """Delete the character matching (owner_id, name).

        Raises:
            CharacterNotFoundError: if no match is found.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(Character).where(
                    Character.owner_id == owner_id,
                    Character.name == name,
                )
            )
            char = result.scalar_one_or_none()

            if char is None:
                raise CharacterNotFoundError(
                    f"Character '{name}' not found for owner '{owner_id}'."
                )

            await session.delete(char)
            await session.commit()

