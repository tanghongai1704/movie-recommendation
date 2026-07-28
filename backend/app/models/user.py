from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Canonical registered user stored in the Users table."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)  # Stable Users partition key and owner ID for user-scoped records.
    email: str = Field(min_length=3)  # Normalized email used for account identification.
    username: str = Field(min_length=1)  # Public account name shown by the application.
    password_hash: str = Field(min_length=1)  # One-way password hash; never returned by an API response.
    created_at: datetime  # UTC time at which the account was created.
    onboarding_genres: list[str]  # Genres selected during first-login onboarding.
    onboarding_completed: bool  # Whether the user has completed required onboarding.
    last_active_at: datetime  # UTC time of the user's most recent authenticated activity.
