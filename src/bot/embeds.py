"""Discord embed builder for character sheets."""

import discord

from bot.db import Character
from bot.validators import ability_modifier


def _fmt_modifier(score: int) -> str:
    """Format an ability score modifier as '+3' or '-1'."""
    mod = ability_modifier(score)
    return f"+{mod}" if mod >= 0 else str(mod)


def _fmt_score(score: int) -> str:
    """Format a score as '18 (+4)'."""
    return f"{score} ({_fmt_modifier(score)})"


def build_character_embed(character: Character) -> discord.Embed:
    """Build and return a rich Discord embed for the given character.

    All values are read directly from the stored ORM object. Ability score
    modifiers are computed here for display only — they are not stored and
    not used for any other logic.
    """
    title = f"⚔️ {character.name}"
    description = (
        f"{character.race} {character.char_class} "
        f"({character.level}) · "
        f"{character.background} · "
        f"{character.alignment}"
    )

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.dark_gold(),
    )

    # --- Ability scores (inline, 3 per row) ---
    embed.add_field(
        name="STR",
        value=_fmt_score(character.strength),
        inline=True,
    )
    embed.add_field(
        name="DEX",
        value=_fmt_score(character.dexterity),
        inline=True,
    )
    embed.add_field(
        name="CON",
        value=_fmt_score(character.constitution),
        inline=True,
    )
    embed.add_field(
        name="INT",
        value=_fmt_score(character.intelligence),
        inline=True,
    )
    embed.add_field(
        name="WIS",
        value=_fmt_score(character.wisdom),
        inline=True,
    )
    embed.add_field(
        name="CHA",
        value=_fmt_score(character.charisma),
        inline=True,
    )

    # --- Combat stats ---
    embed.add_field(name="AC", value=str(character.armor_class), inline=True)
    embed.add_field(name="Speed", value=f"{character.speed} ft", inline=True)
    embed.add_field(
        name="HP",
        value=f"{character.current_hp} / {character.max_hp}",
        inline=True,
    )

    # --- Derived stats ---
    init_sign = "+" if character.initiative >= 0 else ""
    embed.add_field(
        name="Initiative",
        value=f"{init_sign}{character.initiative}",
        inline=True,
    )
    embed.add_field(
        name="Proficiency",
        value=f"+{character.proficiency_bonus}",
        inline=True,
    )
    embed.add_field(
        name="Passive Perception",
        value=str(character.passive_perception),
        inline=True,
    )

    # --- XP ---
    embed.add_field(
        name="Experience Points",
        value=str(character.experience_points),
        inline=False,
    )

    # --- Footer ---
    updated_str = (
        character.updated_at.strftime("%Y-%m-%d")
        if character.updated_at is not None
        else "unknown"
    )
    embed.set_footer(text=f"Updated {updated_str}")

    return embed

