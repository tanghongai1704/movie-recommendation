from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserSettings(BaseModel):
    """Embedded login and audit settings stored in one Users item."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)
    password_hash: str = Field(min_length=1)
    username: str = Field(min_length=1)
    created_at: datetime


class User(BaseModel):
    """Registered user matching the deployed Users schema version 2."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    recent_movie_ids: list[str] = Field(default_factory=list, max_length=100)
    schema_version: int = Field(default=2, ge=1)
    onboarding_genres: list[str] | None = None
    user_settings: UserSettings

    @property
    def email(self) -> str:
        return self.user_settings.email

    @property
    def username(self) -> str:
        return self.user_settings.username

    @property
    def password_hash(self) -> str:
        return self.user_settings.password_hash

    @property
    def created_at(self) -> datetime:
        return self.user_settings.created_at

    @property
    def onboarding_completed(self) -> bool:
        return bool(self.onboarding_genres)

    @property
    def last_active_at(self) -> datetime:
        # The deployed schema has no last_active_at field. Keep the API stable
        # with its closest persisted audit timestamp without writing on login.
        return self.user_settings.created_at
