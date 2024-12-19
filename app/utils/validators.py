from pydantic import BaseModel, validator, ValidationError


class Validators:
    @staticmethod
    def validate_length(value: str, min_length: int = 3, max_length: int = 100) -> str:
        """Validate that the length of a string is within the specified range."""
        if not (min_length <= len(value) <= max_length):
            raise ValueError(
                f"Value must be between {min_length} and {max_length} characters."
            )
        return value

    @staticmethod
    def validate_non_empty(value: str) -> str:
        """Validate that a string is not empty or whitespace."""
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace.")
        return value

    @staticmethod
    def validate_email(value: str) -> str:
        """Validate that a string is a valid email address."""
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address.")
        return value
