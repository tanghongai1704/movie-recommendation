from datetime import datetime, timezone
from enum import Enum
from typing import Any
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

    RECORD = "record"
    SET = "set"
    CLEAR = "clear"

    # Legacy values remain readable so previously persisted interaction events
    # can still be deserialized during migration.
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
    interaction_value: float | None  # Canonical numeric signal; nullable only for legacy records.
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


class StoredUserInteraction(BaseModel):
    """Read-compatible interaction view for canonical and legacy records.

    New writes must continue to use ``UserInteraction``. This model is used
    only when reading an existing DynamoDB user partition, where historical
    records may predate canonical event IDs, actions, session IDs, and field
    names.
    """

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(min_length=1)
    interaction_key: str = Field(min_length=1)
    movie_id: str = Field(min_length=1)
    interaction_type: InteractionType
    interaction_action: InteractionAction
    interaction_value: float | None = None
    timestamp: datetime

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_record(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        record = dict(value)
        interaction_type = record.get("interaction_type")
        if interaction_type is None:
            interaction_type = record.get("event_type")
        record["interaction_type"] = interaction_type

        movie_id = record.get("movie_id")
        if movie_id is not None:
            record["movie_id"] = str(movie_id)

        if record.get("timestamp") is None:
            record["timestamp"] = record.get("created_at")

        interaction_value = record.get("interaction_value")
        if interaction_value is None and record.get("rating") is not None:
            interaction_value = record["rating"]
        if interaction_value is None and interaction_type in {
            InteractionType.CLICK,
            InteractionType.WATCH,
            InteractionType.SHARE,
            InteractionType.CLICK.value,
            InteractionType.WATCH.value,
            InteractionType.SHARE.value,
        }:
            interaction_value = 1.0
        record["interaction_value"] = interaction_value

        interaction_action = record.get("interaction_action")
        if interaction_type in {
            InteractionType.RATING,
            InteractionType.REACTION,
            InteractionType.RATING.value,
            InteractionType.REACTION.value,
        }:
            # Historical datasets sometimes stored a zero-value "set" event.
            # Canonically this means that the previous rating/reaction is clear.
            if interaction_value == 0:
                interaction_action = InteractionAction.CLEAR
            elif interaction_action is None:
                interaction_action = InteractionAction.SET
        elif interaction_action is None:
            interaction_action = InteractionAction.RECORD
        record["interaction_action"] = interaction_action

        return record
