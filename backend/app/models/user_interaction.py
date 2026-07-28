from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InteractionType(str, Enum):
    """Supported user behavior events."""

    CLICK = "click"
    WATCH = "watch"
    RATING = "rating"
    REACTION = "reaction"
    SHARE = "share"


class InteractionAction(str, Enum):
    """Supported actions within each interaction category."""

    OPEN_DETAIL = "open_detail"
    WATCH_START = "start"
    WATCH_PROGRESS = "progress"
    WATCH_COMPLETE = "complete"
    RATING_SUBMIT = "submit"
    REACTION_LIKE = "like"
    REACTION_DISLIKE = "dislike"
    SHARE_NATIVE = "native_share"
    SHARE_COPY_LINK = "copy_link"


def format_interaction_timestamp(value: datetime) -> str:
    """Render a canonical UTC timestamp for the interaction sort key."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("interaction timestamp must include a timezone")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


class UserInteraction(BaseModel):
    """Canonical behavior record stored in the UserInteractions table."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)  # Partition key identifying the registered user who acted.
    interaction_key: str = Field(min_length=5)  # Sort key formatted as timestamp#movie_id#event_id.
    event_id: UUID  # API-generated idempotent event identifier.
    movie_id: str = Field(min_length=1)  # Reference to the interacted Movies.movie_id.
    interaction_type: InteractionType  # Behavior category consumed by analytics and ML.
    interaction_action: InteractionAction  # Concrete action within the behavior category.
    interaction_value: float | None  # Optional numeric value such as rating or watch progress.
    timestamp: datetime  # UTC time at which the behavior occurred.
    session_id: str = Field(min_length=1)  # Client session identifier used to group related behavior.

    @model_validator(mode="after")
    def validate_interaction_key(self) -> "UserInteraction":
        expected_key = (
            f"{format_interaction_timestamp(self.timestamp)}"
            f"#{self.movie_id}#{self.event_id}"
        )
        if self.interaction_key != expected_key:
            raise ValueError(
                "interaction_key must use timestamp#movie_id#event_id"
            )
        return self
