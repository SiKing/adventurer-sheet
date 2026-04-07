"""Custom exception classes for the Adventurer Sheet bot."""


class CharacterNotFoundError(Exception):
    """Raised when a character does not exist for the requesting owner."""


class CharacterAlreadyExistsError(Exception):
    """Raised when a character with the same (owner_id, name) already exists."""


class InvalidFieldError(Exception):
    """Raised when an unrecognised or read-only field name is passed to /character edit.

    For example: attempting to edit 'owner_id' or 'created_at'.
    """


class InvalidValueError(Exception):
    """Raised when a field value fails validation (e.g. level < 1, HP < 1)."""

