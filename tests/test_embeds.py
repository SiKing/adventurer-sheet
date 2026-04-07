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
        assert "Level 5" in embed.description

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

    def test_str_field_shows_score_and_modifier(self) -> None:
        char = _make_character(strength=18)
        embed = build_character_embed(char)
        str_field = next(f for f in embed.fields if f.name == "STR")
        assert "18" in str_field.value
        assert "+4" in str_field.value

    def test_dex_field_shows_modifier(self) -> None:
        char = _make_character(dexterity=10)
        embed = build_character_embed(char)
        dex_field = next(f for f in embed.fields if f.name == "DEX")
        assert "+0" in dex_field.value

    def test_wis_field_shows_negative_modifier(self) -> None:
        char = _make_character(wisdom=8)
        embed = build_character_embed(char)
        wis_field = next(f for f in embed.fields if f.name == "WIS")
        assert "-1" in wis_field.value

    def test_hp_field_shows_current_and_max(self) -> None:
        char = _make_character(current_hp=30, max_hp=52)
        embed = build_character_embed(char)
        hp_field = next(f for f in embed.fields if f.name == "HP")
        assert "30" in hp_field.value
        assert "52" in hp_field.value

    def test_ac_field(self) -> None:
        char = _make_character(armor_class=16)
        embed = build_character_embed(char)
        ac_field = next(f for f in embed.fields if f.name == "AC")
        assert "16" in ac_field.value

    def test_speed_field_shows_feet(self) -> None:
        char = _make_character(speed=25)
        embed = build_character_embed(char)
        speed_field = next(f for f in embed.fields if f.name == "Speed")
        assert "25" in speed_field.value
        assert "ft" in speed_field.value

    def test_initiative_positive_has_plus_sign(self) -> None:
        char = _make_character(initiative=3)
        embed = build_character_embed(char)
        init_field = next(f for f in embed.fields if f.name == "Initiative")
        assert "+3" in init_field.value

    def test_initiative_zero_has_plus_sign(self) -> None:
        char = _make_character(initiative=0)
        embed = build_character_embed(char)
        init_field = next(f for f in embed.fields if f.name == "Initiative")
        assert "+0" in init_field.value

    def test_initiative_negative_has_minus_sign(self) -> None:
        char = _make_character(initiative=-1)
        embed = build_character_embed(char)
        init_field = next(f for f in embed.fields if f.name == "Initiative")
        assert "-1" in init_field.value

    def test_proficiency_field(self) -> None:
        char = _make_character(proficiency_bonus=3)
        embed = build_character_embed(char)
        prof_field = next(f for f in embed.fields if f.name == "Proficiency")
        assert "+3" in prof_field.value

    def test_passive_perception_field(self) -> None:
        char = _make_character(passive_perception=11)
        embed = build_character_embed(char)
        pp_field = next(f for f in embed.fields if f.name == "Passive Perception")
        assert "11" in pp_field.value

    def test_xp_field(self) -> None:
        char = _make_character(experience_points=6500)
        embed = build_character_embed(char)
        xp_field = next(
            f for f in embed.fields if f.name == "Experience Points"
        )
        assert "6500" in xp_field.value

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

    def test_ability_score_fields_are_inline(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        for name in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
            field = next(f for f in embed.fields if f.name == name)
            assert field.inline is True

    def test_xp_field_is_not_inline(self) -> None:
        char = _make_character()
        embed = build_character_embed(char)
        xp_field = next(
            f for f in embed.fields if f.name == "Experience Points"
        )
        assert xp_field.inline is False

