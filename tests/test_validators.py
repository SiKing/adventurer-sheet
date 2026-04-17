"""Tests for src/bot/validators.py — pure validation helpers."""

import pytest

from bot.errors import InvalidFieldError, InvalidValueError
from bot.validators import (
    EDITABLE_FIELDS,
    INTEGER_FIELDS,
    POSITIVE_INT_FIELDS,
    ability_modifier,
    default_passive_perception,
    proficiency_bonus,
    validate_ability_score,
    validate_field_name,
    validate_field_value,
    validate_level,
    validate_positive_int,
)

# ---------------------------------------------------------------------------
# validate_level
# ---------------------------------------------------------------------------


class TestValidateLevel:
    def test_valid_level_one(self) -> None:
        assert validate_level("1") == 1

    def test_valid_level_high(self) -> None:
        assert validate_level("20") == 20

    def test_valid_level_very_high(self) -> None:
        """No upper bound is enforced."""
        assert validate_level("9999") == 9999

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_level("0")

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_level("-5")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_level("abc")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_level("")

    def test_float_string_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_level("3.5")


# ---------------------------------------------------------------------------
# validate_ability_score
# ---------------------------------------------------------------------------


class TestValidateAbilityScore:
    def test_valid_score_one(self) -> None:
        assert validate_ability_score("1") == 1

    def test_valid_score_ten(self) -> None:
        assert validate_ability_score("10") == 10

    def test_valid_score_twenty(self) -> None:
        assert validate_ability_score("20") == 20

    def test_valid_score_very_high(self) -> None:
        """No upper bound is enforced."""
        assert validate_ability_score("30") == 30

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_ability_score("0")

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_ability_score("-1")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_ability_score("strong")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_ability_score("")


# ---------------------------------------------------------------------------
# validate_positive_int
# ---------------------------------------------------------------------------


class TestValidatePositiveInt:
    def test_valid_value(self) -> None:
        assert validate_positive_int("max_hp", "10") == 10

    def test_minimum_one(self) -> None:
        assert validate_positive_int("speed", "1") == 1

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_positive_int("max_hp", "0")

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_positive_int("armor_class", "-10")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_positive_int("speed", "fast")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_positive_int("current_hp", "")

    def test_field_name_in_error_message(self) -> None:
        with pytest.raises(InvalidValueError, match="max_hp"):
            validate_positive_int("max_hp", "abc")


# ---------------------------------------------------------------------------
# validate_field_name
# ---------------------------------------------------------------------------


class TestValidateFieldName:
    @pytest.mark.parametrize(
        "field",
        [
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
        ],
    )
    def test_all_editable_fields_accepted(self, field: str) -> None:
        assert validate_field_name(field) == field

    def test_id_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("id")

    def test_owner_id_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("owner_id")

    def test_created_at_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("created_at")

    def test_updated_at_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("updated_at")

    def test_unknown_field_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("attack_bonus")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_name("")


# ---------------------------------------------------------------------------
# ability_modifier
# ---------------------------------------------------------------------------


class TestAbilityModifier:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (1, -5),
            (8, -1),
            (9, -1),
            (10, 0),
            (11, 0),
            (12, 1),
            (14, 2),
            (16, 3),
            (18, 4),
            (20, 5),
            (30, 10),
        ],
    )
    def test_modifier_values(self, score: int, expected: int) -> None:
        assert ability_modifier(score) == expected


# ---------------------------------------------------------------------------
# proficiency_bonus
# ---------------------------------------------------------------------------


class TestProficiencyBonus:
    @pytest.mark.parametrize(
        "level,expected",
        [
            (1, 2),
            (2, 2),
            (3, 2),
            (4, 2),
            (5, 3),
            (6, 3),
            (7, 3),
            (8, 3),
            (9, 4),
            (10, 4),
            (17, 6),
            (20, 6),
        ],
    )
    def test_bonus_by_level(self, level: int, expected: int) -> None:
        assert proficiency_bonus(level) == expected


# ---------------------------------------------------------------------------
# default_passive_perception
# ---------------------------------------------------------------------------


class TestDefaultPassivePerception:
    def test_wisdom_10_gives_10(self) -> None:
        assert default_passive_perception(10) == 10

    def test_wisdom_14_gives_12(self) -> None:
        assert default_passive_perception(14) == 12

    def test_wisdom_8_gives_9(self) -> None:
        assert default_passive_perception(8) == 9

    def test_wisdom_18_gives_14(self) -> None:
        assert default_passive_perception(18) == 14


# ---------------------------------------------------------------------------
# EDITABLE_FIELDS constant
# ---------------------------------------------------------------------------


class TestEditableFields:
    def test_is_frozenset(self) -> None:
        assert isinstance(EDITABLE_FIELDS, frozenset)

    def test_contains_expected_fields(self) -> None:
        for field in ("name", "level", "strength", "max_hp", "experience_points"):
            assert field in EDITABLE_FIELDS

    def test_excludes_readonly_fields(self) -> None:
        for field in ("id", "owner_id", "created_at", "updated_at"):
            assert field not in EDITABLE_FIELDS


# ---------------------------------------------------------------------------
# INTEGER_FIELDS and POSITIVE_INT_FIELDS constants
# ---------------------------------------------------------------------------


class TestFieldSets:
    def test_integer_fields_is_frozenset(self) -> None:
        assert isinstance(INTEGER_FIELDS, frozenset)

    def test_positive_int_fields_is_frozenset(self) -> None:
        assert isinstance(POSITIVE_INT_FIELDS, frozenset)

    def test_positive_int_fields_subset_of_integer_fields(self) -> None:
        assert POSITIVE_INT_FIELDS <= INTEGER_FIELDS

    def test_integer_fields_subset_of_editable_fields(self) -> None:
        assert INTEGER_FIELDS <= EDITABLE_FIELDS

    def test_initiative_is_integer_but_not_positive(self) -> None:
        """Initiative can be negative (e.g. low DEX)."""
        assert "initiative" in INTEGER_FIELDS
        assert "initiative" not in POSITIVE_INT_FIELDS

    def test_experience_points_is_integer_but_not_positive(self) -> None:
        """XP can be 0."""
        assert "experience_points" in INTEGER_FIELDS
        assert "experience_points" not in POSITIVE_INT_FIELDS


# ---------------------------------------------------------------------------
# validate_field_value
# ---------------------------------------------------------------------------


class TestValidateFieldValue:
    def test_string_field_returns_string(self) -> None:
        assert validate_field_value("alignment", "Chaotic Good") == "Chaotic Good"

    def test_integer_field_returns_int(self) -> None:
        assert validate_field_value("strength", "18") == 18

    def test_positive_int_field_rejects_zero(self) -> None:
        with pytest.raises(InvalidValueError, match="at least 1"):
            validate_field_value("level", "0")

    def test_integer_field_rejects_non_numeric(self) -> None:
        with pytest.raises(InvalidValueError, match="integer"):
            validate_field_value("strength", "abc")

    def test_invalid_field_raises(self) -> None:
        with pytest.raises(InvalidFieldError):
            validate_field_value("owner_id", "999")

    def test_initiative_allows_negative(self) -> None:
        assert validate_field_value("initiative", "-2") == -2

    def test_experience_points_allows_zero(self) -> None:
        assert validate_field_value("experience_points", "0") == 0


