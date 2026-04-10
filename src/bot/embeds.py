"""Discord embed builder for character sheets."""

import discord

from bot.db import Character
from bot.validators import ability_modifier

# Ordered list of (prefix, emoji) pairs — checked with str.startswith.
# Multi-classed characters (e.g. "Fighter/Wizard") match on the first class.
_CLASS_ICONS: list[tuple[str, str]] = [
    ("barbarian", "🪓"),
    ("bard", "🪈"),
    ("cleric", "🍷"),
    ("druid", "🦡"),
    ("fighter", "⚔️"),
    ("monk", "🥋"),
    ("paladin", "🛡️"),
    ("ranger", "🏹"),
    ("rogue", "🗝️"),
    ("sorcerer", "💫"),
    ("warlock", "👿"),
    ("wizard", "🧙"),
]
_DEFAULT_ICON = "🎲"


def _class_icon(char_class: str) -> str:
    """Return the emoji for *char_class* using a starts_with match.

    The comparison is case-insensitive so "Fighter", "fighter", and
    "Fighter/Wizard" all match correctly.
    """
    lowered = char_class.lower()
    for prefix, icon in _CLASS_ICONS:
        if lowered.startswith(prefix):
            return icon
    return _DEFAULT_ICON


def _fmt_modifier(score: int) -> str:
    """Format an ability score modifier as '+3' or '-1'."""
    mod = ability_modifier(score)
    return f"+{mod}" if mod >= 0 else str(mod)


def _fmt_score(score: int) -> str:
    """Format a score as '18 (+4)'."""
    return f"{score:>2} ({_fmt_modifier(score)})"


def build_character_embed(character: Character) -> discord.Embed:
    """Build and return a rich Discord embed for the given character.

    All values are read directly from the stored ORM object. Ability score
    modifiers are computed here for display only — they are not stored and
    not used for any other logic.

    Layout uses compact text blocks inside single fields so the sheet reads
    well on both mobile (no column support) and desktop.
    """
    title = f"{_class_icon(character.char_class)} {character.name}"
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

    # --- Ability scores — two rows of three, monospace table ---
    ability_block = (
        "```\n"
        f"STR {_fmt_score(character.strength)}  "
        f"DEX {_fmt_score(character.dexterity)}  "
        f"CON {_fmt_score(character.constitution)}\n"
        f"INT {_fmt_score(character.intelligence)}  "
        f"WIS {_fmt_score(character.wisdom)}  "
        f"CHA {_fmt_score(character.charisma)}\n"
        "```"
    )
    embed.add_field(name="Ability Scores", value=ability_block, inline=False)

    # --- Combat stats — two rows of three, monospace table ---
    init_sign = "+" if character.initiative >= 0 else ""
    combat_block = (
        "```\n"
        f"AC {character.armor_class}  ·  "
        f"HP {character.current_hp}/{character.max_hp}  ·  "
        f"Speed {character.speed} ft\n"
        f"Init {init_sign}{character.initiative}  ·  "
        f"Prof +{character.proficiency_bonus}  ·  "
        f"Pasve Perc {character.passive_perception}\n"
        "```"
    )
    embed.add_field(name="Combat", value=combat_block, inline=False)

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

