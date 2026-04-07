"""Tests for custom exception classes in bot.errors."""

import pytest

from bot.errors import (
    CharacterAlreadyExistsError,
    CharacterNotFoundError,
    InvalidFieldError,
    InvalidValueError,
)


class TestCharacterNotFoundError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(CharacterNotFoundError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(CharacterNotFoundError):
            raise CharacterNotFoundError("Thorin not found")

    def test_message_preserved(self) -> None:
        with pytest.raises(CharacterNotFoundError, match="Thorin not found"):
            raise CharacterNotFoundError("Thorin not found")


class TestCharacterAlreadyExistsError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(CharacterAlreadyExistsError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(CharacterAlreadyExistsError):
            raise CharacterAlreadyExistsError("Thorin already exists")

    def test_message_preserved(self) -> None:
        with pytest.raises(CharacterAlreadyExistsError, match="Thorin already exists"):
            raise CharacterAlreadyExistsError("Thorin already exists")


class TestInvalidFieldError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(InvalidFieldError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(InvalidFieldError):
            raise InvalidFieldError("'owner_id' is not an editable field")

    def test_message_preserved(self) -> None:
        with pytest.raises(InvalidFieldError, match="owner_id"):
            raise InvalidFieldError("'owner_id' is not an editable field")


class TestInvalidValueError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(InvalidValueError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(InvalidValueError):
            raise InvalidValueError("level must be ≥ 1")

    def test_message_preserved(self) -> None:
        with pytest.raises(InvalidValueError, match="level must be"):
            raise InvalidValueError("level must be ≥ 1")

    def test_all_exceptions_are_distinct_types(self) -> None:
        """Catching one exception type must not accidentally catch another."""
        with pytest.raises(CharacterNotFoundError):
            try:
                raise CharacterNotFoundError("not found")
            except (CharacterAlreadyExistsError, InvalidFieldError, InvalidValueError):
                pytest.fail("Wrong exception type caught")
            except CharacterNotFoundError:
                raise

