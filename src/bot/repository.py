"""Character repository — all database access for the characters table."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.db import Character
from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
)
from bot.validators import (
    ability_modifier as _ability_modifier,
)
from bot.validators import (
    default_passive_perception as _default_passive_perception,
)
from bot.validators import (
    proficiency_bonus as _proficiency_bonus,
)
from bot.validators import (
    validate_field_value,
)

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
        coerced = validate_field_value(field, value)

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

