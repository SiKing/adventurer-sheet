"""Pure validation helpers for character field values.

These functions have no I/O, no Discord dependency, and no database access.
They are used by the repository and the character cog to validate user input.
"""

from bot.errors import InvalidFieldError, InvalidValueError

# ---------------------------------------------------------------------------
# Field metadata — single source of truth for all field sets
# ---------------------------------------------------------------------------

# Fields the player is allowed to edit via /character edit.
# All columns except id, owner_id, created_at, updated_at.
EDITABLE_FIELDS: frozenset[str] = frozenset(
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
INTEGER_FIELDS: frozenset[str] = frozenset(
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
POSITIVE_INT_FIELDS: frozenset[str] = frozenset(
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
# Validators
# ---------------------------------------------------------------------------


def validate_level(value: str) -> int:
    """Parse and validate a level string. Must be an integer ≥ 1.

    Raises:
        InvalidValueError: if the value is not a positive integer.
    """
    try:
        level = int(value)
    except (ValueError, TypeError) as exc:
        raise InvalidValueError(
            f"Level must be an integer, got '{value}'."
        ) from exc
    if level < 1:
        raise InvalidValueError(f"Level must be at least 1, got {level}.")
    return level


def validate_ability_score(value: str) -> int:
    """Parse and validate an ability score string. Must be an integer ≥ 1.

    Raises:
        InvalidValueError: if the value is not a positive integer.
    """
    try:
        score = int(value)
    except (ValueError, TypeError) as exc:
        raise InvalidValueError(
            f"Ability score must be an integer, got '{value}'."
        ) from exc
    if score < 1:
        raise InvalidValueError(
            f"Ability score must be at least 1, got {score}."
        )
    return score


def validate_positive_int(field: str, value: str) -> int:
    """Parse and validate that *value* is a positive integer (> 0) for *field*.

    Raises:
        InvalidValueError: if the value is not a positive integer.
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError) as exc:
        raise InvalidValueError(
            f"'{field}' must be an integer, got '{value}'."
        ) from exc
    if int_value < 1:
        raise InvalidValueError(
            f"'{field}' must be at least 1, got {int_value}."
        )
    return int_value


def validate_field_name(name: str) -> str:
    """Assert that *name* is an editable field name.

    Raises:
        InvalidFieldError: if the field is not in the editable set.
    """
    if name not in EDITABLE_FIELDS:
        raise InvalidFieldError(
            f"'{name}' is not an editable field. "
            "Read-only fields: id, owner_id, created_at, updated_at."
        )
    return name


def validate_field_value(field: str, value: str) -> str | int:
    """Validate and coerce *value* for the given *field*.

    Returns the coerced value (int for integer fields, str for string fields).

    Raises:
        InvalidFieldError: if *field* is not editable.
        InvalidValueError: if *value* fails type or range validation.
    """
    validate_field_name(field)

    if field in INTEGER_FIELDS:
        try:
            coerced = int(value)
        except (ValueError, TypeError) as exc:
            raise InvalidValueError(
                f"'{field}' requires an integer value, got '{value}'."
            ) from exc
        if field in POSITIVE_INT_FIELDS and coerced < 1:
            raise InvalidValueError(
                f"'{field}' must be at least 1, got {coerced}."
            )
        return coerced

    return value


# ---------------------------------------------------------------------------
# Display / default helpers
# ---------------------------------------------------------------------------


def ability_modifier(score: int) -> int:
    """Return the D&D 5e ability modifier for a given score.

    Formula: (score - 10) // 2

    Used to compute initial derived stats at character creation time and for
    display formatting (e.g. '+3' or '-1').
    """
    return (score - 10) // 2


def proficiency_bonus(level: int) -> int:
    """Return the standard proficiency bonus for a given level.

    Formula: 2 + (level - 1) // 4

    Used to compute the initial default at character creation time only.
    """
    return 2 + (level - 1) // 4


def default_passive_perception(wisdom: int) -> int:
    """Return the default passive perception for a given Wisdom score.

    Formula: 10 + ability_modifier(wisdom)

    Used to compute the initial default at character creation time only.
    """
    return 10 + ability_modifier(wisdom)

