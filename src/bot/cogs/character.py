"""Character commands cog — /character create|view|edit|delete|list."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.db import Character
from bot.embeds import build_character_embed
from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
    InvalidFieldError,
    InvalidValueError,
)
from bot.repository import CharacterRepository
from bot.validators import EDITABLE_FIELDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modal — /character create
# ---------------------------------------------------------------------------


class CreateCharacterModal(discord.ui.Modal, title="Create a Character"):
    """5-field modal for character creation."""

    char_name = discord.ui.TextInput(
        label="Character Name",
        placeholder="e.g. Thorin Oakenshield",
        max_length=100,
        required=True,
    )
    char_class = discord.ui.TextInput(
        label="Class",
        placeholder="e.g. Fighter",
        max_length=50,
        required=True,
    )
    char_race = discord.ui.TextInput(
        label="Race",
        placeholder="e.g. Dwarf",
        max_length=50,
        required=True,
    )
    char_background = discord.ui.TextInput(
        label="Background",
        placeholder="e.g. Soldier",
        max_length=50,
        required=True,
    )
    char_alignment = discord.ui.TextInput(
        label="Alignment",
        placeholder="e.g. Lawful Good",
        max_length=20,
        required=True,
    )

    def __init__(
        self,
        *,
        repo: CharacterRepository,
        active_ref: dict[str, str],
    ) -> None:
        super().__init__()
        self._repo = repo
        self._active_ref = active_ref

    async def on_submit(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        owner_id = str(interaction.user.id)
        name = self.char_name.value
        try:
            char: Character = await self._repo.create(
                owner_id=owner_id,
                name=name,
                char_class=self.char_class.value,
                race=self.char_race.value,
                background=self.char_background.value,
                alignment=self.char_alignment.value,
            )
        except CharacterAlreadyExistsError:
            await interaction.response.send_message(
                f"⚠️ You already have a character named **{name}**.",
                ephemeral=True,
            )
            return

        # Set as active character
        self._active_ref[owner_id] = char.name

        await interaction.response.send_message(
            f"✅ **{char.name}** has been created and set as your active character! "
            "Level defaults to 1 and stats to 10 — use "
            "`/character edit` to update them.",
            ephemeral=True,
        )
        logger.info("Created character '%s' for owner %s", char.name, owner_id)


# ---------------------------------------------------------------------------
# View — /character delete confirmation
# ---------------------------------------------------------------------------


class ConfirmDeleteView(discord.ui.View):
    """Two-button confirmation view for /character delete."""

    def __init__(
        self,
        *,
        repo: CharacterRepository,
        owner_id: str,
        character_name: str,
        active_ref: dict[str, str],
    ) -> None:
        super().__init__(timeout=60.0)
        self._repo = repo
        self._owner_id = owner_id
        self._character_name = character_name
        self._active_ref = active_ref

    @discord.ui.button(label="🗑️ Yes, delete", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button  # type: ignore[override]
    ) -> None:
        await self._repo.delete(self._owner_id, self._character_name)

        # Clear active character if the deleted one was active
        if self._active_ref.get(self._owner_id) == self._character_name:
            self._active_ref.pop(self._owner_id, None)

        self.stop()
        await interaction.response.edit_message(
            content=f"🗑️ **{self._character_name}** has been deleted.",
            view=None,
        )
        logger.info(
            "Deleted character '%s' for owner %s",
            self._character_name,
            self._owner_id,
        )

    @discord.ui.button(label="✖ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button  # type: ignore[override]
    ) -> None:
        self.stop()
        await interaction.response.edit_message(
            content="✖ Deletion cancelled.",
            view=None,
        )

    async def on_timeout(self) -> None:
        """Treat timeout as Cancel — stop the view silently."""
        self.stop()


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class CharacterCog(commands.Cog):
    """Cog providing all /character sub-commands."""

    # Class-level group — discord.py binds `self` on sub-commands automatically.
    character_group = app_commands.Group(
        name="character",
        description="Manage your D&D 5e character sheets.",
    )

    def __init__(self, bot: commands.Bot, repo: CharacterRepository) -> None:
        self._bot = bot
        self._repo = repo
        # In-memory active character map: {user_id: character_name}
        self._active: dict[str, str] = {}
        super().__init__()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _set_active(self, user_id: str, name: str) -> None:
        """Set the active character for a user."""
        self._active[user_id] = name

    def _clear_active(self, user_id: str) -> None:
        """Clear the active character entry for a user (no-op if not set)."""
        self._active.pop(user_id, None)

    async def _get_own_character(
        self,
        interaction: discord.Interaction,
        name: str | None,
    ) -> Character:
        """Resolve and return the character owned by interaction.user.

        If *name* is None, falls back to the active character for this user.

        Raises:
            CharacterNotFoundError: if no name can be resolved, or if the
                resolved name does not match any character for this owner.
        """
        owner_id = str(interaction.user.id)

        if name is None:
            name = self._active.get(owner_id)
            if name is None:
                raise CharacterNotFoundError(
                    "No active character. Use `/character view <name>` or "
                    "`/character create` to set one."
                )

        return await self._repo.get_by_name(owner_id, name)

    # ------------------------------------------------------------------
    # /character create
    # ------------------------------------------------------------------

    @character_group.command(
        name="create",
        description="Create a new D&D 5e character (opens a form).",
    )
    async def character_create(self, interaction: discord.Interaction) -> None:
        """Open the character creation modal."""
        modal = CreateCharacterModal(
            repo=self._repo,
            active_ref=self._active,
        )
        await interaction.response.send_modal(modal)

    # ------------------------------------------------------------------
    # /character view [name]
    # ------------------------------------------------------------------

    @character_group.command(
        name="view",
        description="Display your character sheet. Omit name to use your active.",
    )
    @app_commands.describe(name="Character name (optional if you have an active)")
    async def character_view(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
    ) -> None:
        """Fetch and display a character as a rich embed."""
        owner_id = str(interaction.user.id)

        try:
            char = await self._get_own_character(interaction, name)
        except CharacterNotFoundError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        # Update active character
        self._set_active(owner_id, char.name)

        embed = build_character_embed(char)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /character edit [name] <field> <value>
    # ------------------------------------------------------------------

    @character_group.command(
        name="edit",
        description="Edit a field on your character sheet.",
    )
    @app_commands.describe(
        name="Character name (optional if you have an active character)",
        field="Field to edit (e.g. strength, level, alignment)",
        value="New value for the field",
    )
    async def character_edit(
        self,
        interaction: discord.Interaction,
        field: str,
        value: str,
        name: str | None = None,
    ) -> None:
        """Update a single editable field on a character."""
        owner_id = str(interaction.user.id)

        # Resolve the character name first to catch missing active
        try:
            char = await self._get_own_character(interaction, name)
        except CharacterNotFoundError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        try:
            updated = await self._repo.update(owner_id, char.name, field, value)
        except (CharacterNotFoundError, InvalidFieldError, InvalidValueError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ **{updated.name}**'s {field} updated to {value}.",
            ephemeral=True,
        )

    @character_edit.autocomplete("field")
    async def _field_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=f, value=f)
            for f in sorted(EDITABLE_FIELDS)
            if current.lower() in f.lower()
        ][:25]

    # ------------------------------------------------------------------
    # /character delete <name>
    # ------------------------------------------------------------------

    @character_group.command(
        name="delete",
        description="Delete a character (requires explicit name as a safety measure).",
    )
    @app_commands.describe(name="Name of the character to delete")
    async def character_delete(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """Confirm and delete a character."""
        owner_id = str(interaction.user.id)

        try:
            await self._repo.get_by_name(owner_id, name)
        except CharacterNotFoundError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        view = ConfirmDeleteView(
            repo=self._repo,
            owner_id=owner_id,
            character_name=name,
            active_ref=self._active,
        )
        await interaction.response.send_message(
            f"Are you sure you want to delete **{name}**? This cannot be undone.",
            view=view,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /character list
    # ------------------------------------------------------------------

    @character_group.command(
        name="list",
        description="List all your characters.",
    )
    async def character_list(self, interaction: discord.Interaction) -> None:
        """List all characters owned by the requesting user."""
        owner_id = str(interaction.user.id)
        characters = await self._repo.list_by_owner(owner_id)

        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet. "
                "Use `/character create` to make one!",
                ephemeral=True,
            )
            return

        lines = [
            f"• **{c.name}** — {c.race} {c.char_class} ({c.level})"
            for c in characters
        ]
        embed = discord.Embed(
            title="Your Characters",
            description="\n".join(lines),
            color=discord.Color.dark_gold(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    """Called by bot.load_extension to register the cog."""
    # The session_factory is injected by __main__.py before load_extension.
    repo: CharacterRepository = bot.__dict__["_character_repo"]
    cog = CharacterCog(bot, repo)
    await bot.add_cog(cog)

