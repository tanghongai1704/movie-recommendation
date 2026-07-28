from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.auth_validation import normalize_email


class UserState(str, Enum):
    """Authenticated user states derived from onboarding completion."""

    FIRST_LOGIN = "first_login"
    RETURNING_USER = "returning_user"


class UserProfileResponse(BaseModel):
    """Safe API representation of a registered user."""

    user_id: str
    email: str
    username: str
    created_at: datetime
    onboarding_genres: list[str]
    onboarding_completed: bool
    last_active_at: datetime
    user_state: UserState


class UpdateProfileRequest(BaseModel):
    """Editable account fields."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str | None = Field(default=None, min_length=3, max_length=254)
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=40,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value is not None else None

    @model_validator(mode="after")
    def require_update(self) -> "UpdateProfileRequest":
        if self.email is None and self.username is None:
            raise ValueError("at least one profile field must be provided")
        return self


class CompleteOnboardingRequest(BaseModel):
    """Genre preferences required to complete first-login onboarding."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    onboarding_genres: list[str] = Field(min_length=1, max_length=3)

    @field_validator("onboarding_genres")
    @classmethod
    def normalize_genres(cls, genres: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for genre in genres:
            value = genre.strip()
            if not value:
                raise ValueError("onboarding genres must not be empty")
            key = value.casefold()
            if key not in seen:
                normalized.append(value)
                seen.add(key)
        return normalized
