"""Pure validation helpers for character field values.

These functions have no I/O, no Discord dependency, and no database access.
They are used by the repository and the character cog to validate user input.
"""

from bot.errors import InvalidFieldError, InvalidValueError

# ---------------------------------------------------------------------------
# Editable field set — mirrors repository._EDITABLE_FIELDS
# ---------------------------------------------------------------------------

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

