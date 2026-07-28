from datetime import datetime

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    """Safe API representation of a registered user."""

    user_id: str  # Stable Users.user_id returned to the authenticated client.
    email: str  # Account email; password_hash is intentionally never exposed.
    username: str  # Public account name.
    created_at: datetime  # UTC account creation time.
    onboarding_genres: list[str]  # Genres selected during onboarding.
    onboarding_completed: bool  # Whether onboarding requirements are complete.
    last_active_at: datetime  # UTC time of the latest authenticated activity.
