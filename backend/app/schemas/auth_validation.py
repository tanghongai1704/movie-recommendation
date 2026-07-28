import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    """Normalize and validate an account email without optional dependencies."""

    normalized = value.strip().casefold()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("email must be valid")
    return normalized
