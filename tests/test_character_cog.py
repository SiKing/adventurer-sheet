"""Tests for src/bot/cogs/character.py — CharacterCog with mocked repository."""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import discord
import pytest

from bot.cogs.character import CharacterCog
from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
    InvalidFieldError,
    InvalidValueError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_character(**kwargs) -> MagicMock:
    """Build a Character-like MagicMock stub with sensible defaults."""
    defaults = dict(
        id=1,
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
        created_at=datetime(2026, 4, 7),
        updated_at=datetime(2026, 4, 7),
    )
    defaults.update(kwargs)
    char = MagicMock()
    for k, v in defaults.items():
        setattr(char, k, v)
    return char


def _make_interaction(user_id: str = "111111111111111111") -> MagicMock:
    """Return a mock discord.Interaction with a user whose id is user_id."""
    interaction = MagicMock(spec=discord.Interaction)
    user = MagicMock()
    user.id = int(user_id)
    user.name = "testuser"
    interaction.user = user
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    return interaction


def _make_repo() -> MagicMock:
    """Return an AsyncMock CharacterRepository."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_name = AsyncMock()
    repo.list_by_owner = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


def _make_cog(repo=None) -> CharacterCog:
    """Instantiate CharacterCog with a mock bot and optional mock repo."""
    bot = MagicMock()
    if repo is None:
        repo = _make_repo()
    return CharacterCog(bot, repo)


# ---------------------------------------------------------------------------
# _get_own_character helper (tested via command paths)
# ---------------------------------------------------------------------------


class TestGetOwnCharacter:
    """Test the private helper indirectly through command calls."""

    @pytest.mark.asyncio
    async def test_resolves_name_from_active_when_none(self) -> None:
        """When name=None and active character is set, uses active name."""
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Thorin")
        cog = _make_cog(repo)
        interaction = _make_interaction()
        user_id = str(interaction.user.id)

        # Set active character
        cog._active[user_id] = "Thorin"

        char = await cog._get_own_character(interaction, None)
        assert char.name == "Thorin"
        repo.get_by_name.assert_awaited_once_with(user_id, "Thorin")

    @pytest.mark.asyncio
    async def test_raises_when_name_none_and_no_active(self) -> None:
        """When name=None and no active character, raises CharacterNotFoundError."""
        cog = _make_cog()
        interaction = _make_interaction()

        with pytest.raises(CharacterNotFoundError):
            await cog._get_own_character(interaction, None)

    @pytest.mark.asyncio
    async def test_uses_provided_name(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Gandalf")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        char = await cog._get_own_character(interaction, "Gandalf")
        assert char.name == "Gandalf"


# ---------------------------------------------------------------------------
# /character list
# ---------------------------------------------------------------------------


class TestCharacterList:
    @pytest.mark.asyncio
    async def test_list_no_characters(self) -> None:
        repo = _make_repo()
        repo.list_by_owner.return_value = []
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_list.callback(cog, interaction)

        interaction.response.send_message.assert_awaited_once()
        args, kwargs = interaction.response.send_message.call_args
        msg = (args[0] if args else kwargs.get("content", "")).lower()
        assert "character" in msg

    @pytest.mark.asyncio
    async def test_list_with_characters_returns_embed(self) -> None:
        repo = _make_repo()
        repo.list_by_owner.return_value = [
            _make_character(name="Thorin"),
            _make_character(name="Gandalf", char_class="Wizard"),
        ]
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_list.callback(cog, interaction)

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        embed = kwargs.get("embed")
        assert embed is not None
        assert "Thorin" in embed.description
        assert "Gandalf" in embed.description


# ---------------------------------------------------------------------------
# /character view
# ---------------------------------------------------------------------------


class TestCharacterView:
    @pytest.mark.asyncio
    async def test_view_by_name_sends_embed(self) -> None:
        repo = _make_repo()
        char = _make_character(name="Thorin")
        repo.get_by_name.return_value = char
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_view.callback(cog, interaction, name="Thorin")

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert isinstance(kwargs.get("embed"), discord.Embed)

    @pytest.mark.asyncio
    async def test_view_sets_active_character(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Thorin")
        cog = _make_cog(repo)
        interaction = _make_interaction()
        user_id = str(interaction.user.id)

        await cog.character_view.callback(cog, interaction, name="Thorin")

        assert cog._active[user_id] == "Thorin"

    @pytest.mark.asyncio
    async def test_view_no_name_uses_active(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Thorin")
        cog = _make_cog(repo)
        interaction = _make_interaction()
        user_id = str(interaction.user.id)
        cog._active[user_id] = "Thorin"

        await cog.character_view.callback(cog, interaction, name=None)

        repo.get_by_name.assert_awaited_once_with(user_id, "Thorin")

    @pytest.mark.asyncio
    async def test_view_no_name_no_active_replies_ephemeral(self) -> None:
        repo = _make_repo()
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_view.callback(cog, interaction, name=None)

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_view_not_found_replies_ephemeral(self) -> None:
        repo = _make_repo()
        repo.get_by_name.side_effect = CharacterNotFoundError("not found")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_view.callback(cog, interaction, name="Nobody")

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# /character edit
# ---------------------------------------------------------------------------


class TestCharacterEdit:
    @pytest.mark.asyncio
    async def test_edit_updates_field(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Thorin", strength=18)
        updated = _make_character(name="Thorin", strength=20)
        repo.update.return_value = updated
        cog = _make_cog(repo)
        interaction = _make_interaction()
        user_id = str(interaction.user.id)
        cog._active[user_id] = "Thorin"

        await cog.character_edit.callback(
            cog, interaction, name=None, field="strength", value="20"
        )

        repo.update.assert_awaited_once()
        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_edit_no_name_uses_active(self) -> None:
        repo = _make_repo()
        char = _make_character(name="Thorin")
        repo.get_by_name.return_value = char
        repo.update.return_value = char
        cog = _make_cog(repo)
        interaction = _make_interaction()
        user_id = str(interaction.user.id)
        cog._active[user_id] = "Thorin"

        await cog.character_edit.callback(
            cog, interaction, name=None, field="level", value="6"
        )

        repo.update.assert_awaited_once_with(user_id, "Thorin", "level", "6")

    @pytest.mark.asyncio
    async def test_edit_no_name_no_active_replies_ephemeral(self) -> None:
        cog = _make_cog()
        interaction = _make_interaction()

        await cog.character_edit.callback(
            cog, interaction, name=None, field="strength", value="18"
        )

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_edit_not_found_replies_ephemeral(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character()
        repo.update.side_effect = CharacterNotFoundError("not found")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_edit.callback(
            cog, interaction, name="Nobody", field="strength", value="18"
        )

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_edit_invalid_field_replies_ephemeral(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character()
        repo.update.side_effect = InvalidFieldError("bad field")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_edit.callback(
            cog, interaction, name="Thorin", field="owner_id", value="999"
        )

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_edit_invalid_value_replies_ephemeral(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character()
        repo.update.side_effect = InvalidValueError("bad value")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_edit.callback(
            cog, interaction, name="Thorin", field="level", value="abc"
        )

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# /character delete
# ---------------------------------------------------------------------------


class TestCharacterDelete:
    @pytest.mark.asyncio
    async def test_delete_sends_confirmation_view(self) -> None:
        repo = _make_repo()
        repo.get_by_name.return_value = _make_character(name="Thorin")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_delete.callback(cog, interaction, name="Thorin")

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        # Should include a View and be ephemeral
        assert kwargs.get("ephemeral") is True
        assert kwargs.get("view") is not None

    @pytest.mark.asyncio
    async def test_delete_not_found_replies_ephemeral(self) -> None:
        repo = _make_repo()
        repo.get_by_name.side_effect = CharacterNotFoundError("not found")
        cog = _make_cog(repo)
        interaction = _make_interaction()

        await cog.character_delete.callback(cog, interaction, name="Nobody")

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True
        # No view on error
        assert kwargs.get("view") is None or isinstance(kwargs.get("view"), type(None))

    @pytest.mark.asyncio
    async def test_delete_confirm_removes_character(self) -> None:
        """Clicking Confirm calls repo.delete and edits the message."""
        from bot.cogs.character import ConfirmDeleteView

        repo = _make_repo()
        cog = _make_cog(repo)
        user_id = "111111111111111111"
        cog._active[user_id] = "Thorin"

        view = ConfirmDeleteView(
            repo=repo,
            owner_id=user_id,
            character_name="Thorin",
            active_ref=cog._active,
        )

        interaction = _make_interaction(user_id)
        # discord.py @ui.button wraps the method into a Button item; invoke via .callback
        await view.confirm.callback(interaction)

        repo.delete.assert_awaited_once_with(user_id, "Thorin")
        interaction.response.edit_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_confirm_clears_active_if_active_character(self) -> None:
        """After confirming delete of the active character, active is cleared."""
        from bot.cogs.character import ConfirmDeleteView

        repo = _make_repo()
        cog = _make_cog(repo)
        user_id = "111111111111111111"
        cog._active[user_id] = "Thorin"

        view = ConfirmDeleteView(
            repo=repo,
            owner_id=user_id,
            character_name="Thorin",
            active_ref=cog._active,
        )

        interaction = _make_interaction(user_id)
        await view.confirm.callback(interaction)

        assert user_id not in cog._active

    @pytest.mark.asyncio
    async def test_delete_confirm_does_not_clear_different_active(self) -> None:
        """Delete of a non-active character leaves the active entry intact."""
        from bot.cogs.character import ConfirmDeleteView

        repo = _make_repo()
        cog = _make_cog(repo)
        user_id = "111111111111111111"
        cog._active[user_id] = "Gandalf"  # different active

        view = ConfirmDeleteView(
            repo=repo,
            owner_id=user_id,
            character_name="Thorin",  # deleting a non-active character
            active_ref=cog._active,
        )

        interaction = _make_interaction(user_id)
        await view.confirm.callback(interaction)

        assert cog._active.get(user_id) == "Gandalf"

    @pytest.mark.asyncio
    async def test_delete_cancel_does_not_delete(self) -> None:
        """Clicking Cancel must not call repo.delete."""
        from bot.cogs.character import ConfirmDeleteView

        repo = _make_repo()
        cog = _make_cog(repo)
        user_id = "111111111111111111"

        view = ConfirmDeleteView(
            repo=repo,
            owner_id=user_id,
            character_name="Thorin",
            active_ref=cog._active,
        )

        interaction = _make_interaction(user_id)
        await view.cancel.callback(interaction)

        repo.delete.assert_not_awaited()
        interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# /character create (modal path — tested via modal submit)
# ---------------------------------------------------------------------------


class TestCreateCharacterModal:
    @pytest.mark.asyncio
    async def test_modal_submit_creates_character_and_sets_active(self) -> None:
        """on_submit calls repo.create and sets the active character."""
        from bot.cogs.character import CreateCharacterModal

        repo = _make_repo()
        repo.create.return_value = _make_character(name="Thorin")
        cog = _make_cog(repo)

        modal = CreateCharacterModal(repo=repo, active_ref=cog._active)

        # Simulate filled modal fields
        modal.char_name.default = "Thorin"
        modal.char_class.default = "Fighter"
        modal.char_race.default = "Dwarf"
        modal.char_background.default = "Soldier"
        modal.char_alignment.default = "Lawful Good"

        # Give the TextInput objects a `value` attribute as Discord would
        modal.char_name._value = "Thorin"
        modal.char_class._value = "Fighter"
        modal.char_race._value = "Dwarf"
        modal.char_background._value = "Soldier"
        modal.char_alignment._value = "Lawful Good"

        interaction = _make_interaction()
        user_id = str(interaction.user.id)

        await modal.on_submit(interaction)

        repo.create.assert_awaited_once()
        assert cog._active.get(user_id) == "Thorin"
        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_modal_submit_duplicate_name_replies_error(self) -> None:
        """on_submit replies ephemeral when the name already exists."""
        from bot.cogs.character import CreateCharacterModal

        repo = _make_repo()
        repo.create.side_effect = CharacterAlreadyExistsError("exists")
        cog = _make_cog(repo)

        modal = CreateCharacterModal(repo=repo, active_ref=cog._active)
        modal.char_name._value = "Thorin"
        modal.char_class._value = "Fighter"
        modal.char_race._value = "Dwarf"
        modal.char_background._value = "Soldier"
        modal.char_alignment._value = "Lawful Good"

        interaction = _make_interaction()

        await modal.on_submit(interaction)

        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_create_command_sends_modal(self) -> None:
        """/character create should send a modal."""
        cog = _make_cog()
        interaction = _make_interaction()

        await cog.character_create.callback(cog, interaction)

        interaction.response.send_modal.assert_awaited_once()


# ---------------------------------------------------------------------------
# Active character helpers
# ---------------------------------------------------------------------------


class TestActiveCharacterHelpers:
    def test_set_active(self) -> None:
        cog = _make_cog()
        cog._set_active("111", "Thorin")
        assert cog._active["111"] == "Thorin"

    def test_clear_active(self) -> None:
        cog = _make_cog()
        cog._active["111"] = "Thorin"
        cog._clear_active("111")
        assert "111" not in cog._active

    def test_clear_active_noop_when_not_set(self) -> None:
        cog = _make_cog()
        cog._clear_active("111")  # should not raise
        assert "111" not in cog._active

