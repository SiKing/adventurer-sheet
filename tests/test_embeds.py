"""Tests for src/bot/embeds.py — Discord embed builder."""

from datetime import datetime
from types import SimpleNamespace

from bot.embeds import build_character_embed


def _make_character(**kwargs) -> SimpleNamespace:
    """Construct a Character-like object with sensible defaults for testing.

    Uses SimpleNamespace so we can set arbitrary attributes without triggering
    SQLAlchemy's instrumented descriptor machinery.
    """
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
        created_at=datetime(2026, 4, 7, 12, 0, 0),
        updated_at=datetime(2026, 4, 7, 15, 30, 0),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _ability_field(embed) -> str:
    """Return the value of the 'Ability Scores' field."""
    return next(f for f in embed.fields if f.name == "Ability Scores").value


def _combat_field(embed) -> str:
    """Return the value of the 'Combat' field."""
    return next(f for f in embed.fields if f.name == "Combat").value


class TestBuildCharacterEmbed:
    def test_title_contains_character_name(self) -> None:
        char = _make_character(name="Thorin")
        embed = build_character_embed(char)
        assert "Thorin" in embed.title

    def test_title_has_sword_emoji(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        assert "⚔️" in embed.title

    def test_description_contains_race(self) -> None:
        char = _make_character(race="Dwarf")
        embed = build_character_embed(char)
        assert "Dwarf" in embed.description

    def test_description_contains_class(self) -> None:
        char = _make_character(char_class="Fighter")
        embed = build_character_embed(char)
        assert "Fighter" in embed.description

    def test_description_contains_level(self) -> None:
        char = _make_character(level=5)
        embed = build_character_embed(char)
        assert "(5)" in embed.description

    def test_description_contains_background(self) -> None:
        char = _make_character(background="Soldier")
        embed = build_character_embed(char)
        assert "Soldier" in embed.description

    def test_description_contains_alignment(self) -> None:
        char = _make_character(alignment="Lawful Good")
        embed = build_character_embed(char)
        assert "Lawful Good" in embed.description

    def test_color_is_dark_gold(self) -> None:
        import discord

        char = _make_character()
        embed = build_character_embed(char)
        assert embed.color == discord.Color.dark_gold()

    # --- Ability scores block ---

    def test_ability_block_contains_str_label(self) -> None:
        char = _make_character(strength=18)
        embed = build_character_embed(char)
        assert "STR" in _ability_field(embed)

    def test_ability_block_shows_str_score_and_modifier(self) -> None:
        char = _make_character(strength=18)
        embed = build_character_embed(char)
        value = _ability_field(embed)
        assert "18" in value
        assert "+4" in value

    def test_ability_block_shows_dex_modifier(self) -> None:
        char = _make_character(dexterity=10)
        embed = build_character_embed(char)
        assert "+0" in _ability_field(embed)

    def test_ability_block_shows_negative_modifier(self) -> None:
        char = _make_character(wisdom=8)
        embed = build_character_embed(char)
        assert "-1" in _ability_field(embed)

    def test_ability_block_contains_all_six_labels(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        value = _ability_field(embed)
        for label in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
            assert label in value

    def test_ability_block_is_not_inline(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        field = next(f for f in embed.fields if f.name == "Ability Scores")
        assert field.inline is False

    # --- Combat block ---

    def test_combat_block_shows_hp(self) -> None:
        char = _make_character(current_hp=30, max_hp=52)
        embed = build_character_embed(char)
        value = _combat_field(embed)
        assert "30" in value
        assert "52" in value

    def test_combat_block_shows_ac(self) -> None:
        char = _make_character(armor_class=16)
        embed = build_character_embed(char)
        assert "16" in _combat_field(embed)

    def test_combat_block_shows_speed_with_ft(self) -> None:
        char = _make_character(speed=25)
        embed = build_character_embed(char)
        value = _combat_field(embed)
        assert "25" in value
        assert "ft" in value

    def test_combat_block_initiative_positive_has_plus_sign(self) -> None:
        char = _make_character(initiative=3)
        embed = build_character_embed(char)
        assert "+3" in _combat_field(embed)

    def test_combat_block_initiative_zero_has_plus_sign(self) -> None:
        char = _make_character(initiative=0)
        embed = build_character_embed(char)
        assert "+0" in _combat_field(embed)

    def test_combat_block_initiative_negative_has_minus_sign(self) -> None:
        char = _make_character(initiative=-1)
        embed = build_character_embed(char)
        assert "-1" in _combat_field(embed)

    def test_combat_block_shows_proficiency(self) -> None:
        char = _make_character(proficiency_bonus=3)
        embed = build_character_embed(char)
        assert "+3" in _combat_field(embed)

    def test_combat_block_shows_passive_perception(self) -> None:
        char = _make_character(passive_perception=11)
        embed = build_character_embed(char)
        assert "11" in _combat_field(embed)

    def test_combat_block_is_not_inline(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        field = next(f for f in embed.fields if f.name == "Combat")
        assert field.inline is False

    # --- XP field ---

    def test_xp_field(self) -> None:
        char = _make_character(experience_points=6500)
        embed = build_character_embed(char)
        xp_field = next(
            f for f in embed.fields if f.name == "Experience Points"
        )
        assert "6500" in xp_field.value

    def test_xp_field_is_not_inline(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        xp_field = next(
            f for f in embed.fields if f.name == "Experience Points"
        )
        assert xp_field.inline is False

    # --- Footer ---

    def test_footer_contains_updated_date(self) -> None:
        char = _make_character(updated_at=datetime(2026, 4, 7, 15, 30, 0))
        embed = build_character_embed(char)
        assert "2026-04-07" in embed.footer.text

    def test_footer_handles_none_updated_at(self) -> None:
        char = _make_character(updated_at=None)
        embed = build_character_embed(char)
        assert "unknown" in embed.footer.text

    def test_returns_discord_embed(self) -> None:
        import discord

        char = _make_character()
        embed = build_character_embed(char)
        assert isinstance(embed, discord.Embed)


