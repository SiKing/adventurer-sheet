"""Integration tests for CharacterRepository."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
    InvalidFieldError,
    InvalidValueError,
)
from bot.repository import CharacterRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_repo(session_factory: async_sessionmaker) -> CharacterRepository:
    return CharacterRepository(session_factory)


async def _create_default(
    repo: CharacterRepository,
    owner_id: str = "100000000000000001",
    name: str = "Thorin",
):
    """Create a character with sensible defaults for use in multiple tests."""
    return await repo.create(
        owner_id=owner_id,
        name=name,
        char_class="Fighter",
        race="Dwarf",
        background="Soldier",
        alignment="Lawful Good",
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------

class TestCreate:
    async def test_create_returns_character(self, session_factory) -> None:
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.name == "Thorin"
        assert char.owner_id == "100000000000000001"

    async def test_create_sets_level_default(self, session_factory) -> None:
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.level == 1

    async def test_create_sets_ability_score_defaults(self, session_factory) -> None:
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        for attr in ("strength", "dexterity", "constitution",
                     "intelligence", "wisdom", "charisma"):
            assert getattr(char, attr) == 10

    async def test_create_computes_initiative_from_dex(self, session_factory) -> None:
        """initiative = (dexterity - 10) // 2; with dex=10 → 0."""
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.initiative == 0

    async def test_create_computes_proficiency_bonus(self, session_factory) -> None:
        """proficiency_bonus = 2 + (level-1)//4; level=1 → 2."""
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.proficiency_bonus == 2

    async def test_create_computes_passive_perception(self, session_factory) -> None:
        """passive_perception = 10 + (wisdom-10)//2; wisdom=10 → 10."""
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.passive_perception == 10

    async def test_create_duplicate_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(CharacterAlreadyExistsError):
            await _create_default(repo)

    async def test_create_same_name_different_owner_allowed(
        self, session_factory
    ) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001")
        char2 = await _create_default(repo, owner_id="200000000000000002")
        assert char2.owner_id == "200000000000000002"

    async def test_create_assigns_id(self, session_factory) -> None:
        repo = make_repo(session_factory)
        char = await _create_default(repo)
        assert char.id is not None
        assert char.id > 0

    async def test_create_with_custom_level_adjusts_proficiency(
        self, session_factory
    ) -> None:
        """level=5 → proficiency_bonus = 2 + (5-1)//4 = 3."""
        repo = make_repo(session_factory)
        char = await repo.create(
            owner_id="100000000000000001",
            name="Gandalf",
            char_class="Wizard",
            race="Human",
            background="Sage",
            alignment="Neutral Good",
            level=5,
        )
        assert char.proficiency_bonus == 3

    async def test_create_with_high_dex_adjusts_initiative(
        self, session_factory
    ) -> None:
        """dexterity=16 → initiative = (16-10)//2 = 3."""
        repo = make_repo(session_factory)
        char = await repo.create(
            owner_id="100000000000000001",
            name="Legolas",
            char_class="Ranger",
            race="Elf",
            background="Outlander",
            alignment="Chaotic Good",
            dexterity=16,
        )
        assert char.initiative == 3

    async def test_create_with_high_wisdom_adjusts_passive_perception(
        self, session_factory
    ) -> None:
        """wisdom=14 → passive_perception = 10 + (14-10)//2 = 12."""
        repo = make_repo(session_factory)
        char = await repo.create(
            owner_id="100000000000000001",
            name="Merlin",
            char_class="Druid",
            race="Human",
            background="Hermit",
            alignment="True Neutral",
            wisdom=14,
        )
        assert char.passive_perception == 12


# ---------------------------------------------------------------------------
# get_by_name()
# ---------------------------------------------------------------------------

class TestGetByName:
    async def test_get_existing_character(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        char = await repo.get_by_name("100000000000000001", "Thorin")
        assert char.name == "Thorin"

    async def test_get_not_found_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        with pytest.raises(CharacterNotFoundError):
            await repo.get_by_name("100000000000000001", "Nobody")

    async def test_get_wrong_owner_raises(self, session_factory) -> None:
        """A character is invisible to a different owner — not found."""
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001")
        with pytest.raises(CharacterNotFoundError):
            await repo.get_by_name("200000000000000002", "Thorin")


# ---------------------------------------------------------------------------
# list_by_owner()
# ---------------------------------------------------------------------------

class TestListByOwner:
    async def test_returns_empty_list_for_new_owner(self, session_factory) -> None:
        repo = make_repo(session_factory)
        result = await repo.list_by_owner("100000000000000001")
        assert result == []

    async def test_returns_only_owners_characters(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001", name="Thorin")
        await _create_default(repo, owner_id="100000000000000001", name="Gandalf")
        await _create_default(repo, owner_id="200000000000000002", name="Legolas")

        result = await repo.list_by_owner("100000000000000001")
        names = [c.name for c in result]
        assert sorted(names) == ["Gandalf", "Thorin"]

    async def test_returns_characters_ordered_by_name(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001", name="Zara")
        await _create_default(repo, owner_id="100000000000000001", name="Aerin")
        await _create_default(repo, owner_id="100000000000000001", name="Mira")

        result = await repo.list_by_owner("100000000000000001")
        names = [c.name for c in result]
        assert names == ["Aerin", "Mira", "Zara"]


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------

class TestUpdate:
    async def test_update_string_field(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        char = await repo.update("100000000000000001", "Thorin", "alignment", "Chaotic Good")
        assert char.alignment == "Chaotic Good"

    async def test_update_integer_field(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        char = await repo.update("100000000000000001", "Thorin", "strength", "18")
        assert char.strength == 18

    async def test_update_level(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        char = await repo.update("100000000000000001", "Thorin", "level", "5")
        assert char.level == 5

    async def test_update_not_found_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        with pytest.raises(CharacterNotFoundError):
            await repo.update("100000000000000001", "Nobody", "strength", "18")

    async def test_update_invalid_field_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(InvalidFieldError):
            await repo.update("100000000000000001", "Thorin", "owner_id", "999")

    async def test_update_readonly_field_raises(self, session_factory) -> None:
        """created_at is read-only and must raise InvalidFieldError."""
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(InvalidFieldError):
            await repo.update("100000000000000001", "Thorin", "created_at", "2020-01-01")

    async def test_update_invalid_value_for_integer_field_raises(
        self, session_factory
    ) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(InvalidValueError):
            await repo.update("100000000000000001", "Thorin", "strength", "not_a_number")

    async def test_update_level_below_minimum_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(InvalidValueError):
            await repo.update("100000000000000001", "Thorin", "level", "0")

    async def test_update_hp_below_minimum_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        with pytest.raises(InvalidValueError):
            await repo.update("100000000000000001", "Thorin", "max_hp", "0")

    async def test_update_wrong_owner_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001")
        with pytest.raises(CharacterNotFoundError):
            await repo.update("200000000000000002", "Thorin", "strength", "18")


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

class TestDelete:
    async def test_delete_removes_character(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo)
        await repo.delete("100000000000000001", "Thorin")
        with pytest.raises(CharacterNotFoundError):
            await repo.get_by_name("100000000000000001", "Thorin")

    async def test_delete_not_found_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        with pytest.raises(CharacterNotFoundError):
            await repo.delete("100000000000000001", "Nobody")

    async def test_delete_wrong_owner_raises(self, session_factory) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, owner_id="100000000000000001")
        with pytest.raises(CharacterNotFoundError):
            await repo.delete("200000000000000002", "Thorin")

    async def test_delete_does_not_affect_other_characters(
        self, session_factory
    ) -> None:
        repo = make_repo(session_factory)
        await _create_default(repo, name="Thorin")
        await _create_default(repo, name="Gandalf")
        await repo.delete("100000000000000001", "Thorin")
        chars = await repo.list_by_owner("100000000000000001")
        assert len(chars) == 1
        assert chars[0].name == "Gandalf"

