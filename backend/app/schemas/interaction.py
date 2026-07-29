from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.user_interaction import InteractionType


class InteractionWriteAction(str, Enum):
    """Canonical actions accepted for new interaction writes."""

    RECORD = "record"
    SET = "set"
    CLEAR = "clear"


ALLOWED_ACTIONS = {
    InteractionType.CLICK: {InteractionWriteAction.RECORD},
    InteractionType.WATCH: {InteractionWriteAction.RECORD},
    InteractionType.RATING: {
        InteractionWriteAction.SET,
        InteractionWriteAction.CLEAR,
    },
    InteractionType.REACTION: {
        InteractionWriteAction.SET,
        InteractionWriteAction.CLEAR,
    },
    InteractionType.SHARE: {InteractionWriteAction.RECORD},
}


class InteractionCreate(BaseModel):
    """Request DTO for recording a canonical interaction."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    interaction_type: InteractionType = Field(
        validation_alias=AliasChoices("interaction_type", "event_type"),
    )  # Canonical behavior category; event_type remains an input-only migration alias.
    interaction_action: InteractionWriteAction  # Canonical record, set, or clear action.
    movie_id: str = Field(min_length=1, pattern=r"^[^#]+$")  # Canonical Movies.movie_id reference.
    interaction_value: float | None = Field(
        default=None,
        validation_alias=AliasChoices("interaction_value", "rating"),
    )  # Required canonical signal; rating remains an input-only migration alias.
    timestamp: datetime  # Stable event time supplied with every retry.
    session_id: str = Field(min_length=1, max_length=128)  # Client session grouping identifier.

    @field_validator("movie_id", mode="before")
    @classmethod
    def normalize_movie_id(cls, value: object) -> str:
        """Normalize legacy numeric identifiers to the canonical string type."""

        return str(value)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        """Require an unambiguous timestamp and normalize it to UTC."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_interaction_semantics(self) -> "InteractionCreate":
        if self.interaction_action not in ALLOWED_ACTIONS[self.interaction_type]:
            raise ValueError(
                f"interaction_action '{self.interaction_action.value}' is not valid "
                f"for interaction_type '{self.interaction_type.value}'"
            )

        if self.interaction_value is None:
            raise ValueError("interaction_value is required")

        if self.interaction_type in {
            InteractionType.CLICK,
            InteractionType.SHARE,
        } and self.interaction_value != 1:
            raise ValueError("click and share interaction_value must be 1")

        if self.interaction_type == InteractionType.WATCH and not (
            0 <= self.interaction_value <= 1
        ):
            raise ValueError(
                "watch interaction_value must be a progress ratio from 0 to 1"
            )

        if self.interaction_type == InteractionType.RATING:
            if self.interaction_action == InteractionWriteAction.CLEAR:
                if self.interaction_value != 0:
                    raise ValueError(
                        "cleared rating interaction_value must be 0"
                    )
            elif not 0.5 <= self.interaction_value <= 5.0:
                raise ValueError(
                    "set rating interaction_value must be between 0.5 and 5.0"
                )
            elif not (self.interaction_value * 2).is_integer():
                raise ValueError(
                    "set rating interaction_value must use 0.5 increments"
                )

        if self.interaction_type == InteractionType.REACTION:
            if self.interaction_action == InteractionWriteAction.CLEAR:
                if self.interaction_value != 0:
                    raise ValueError(
                        "cleared reaction interaction_value must be 0"
                    )
            elif self.interaction_value not in {-1, 1}:
                raise ValueError(
                    "set reaction interaction_value must be 1 or -1"
                )
        return self


class InteractionResponse(BaseModel):
    """API response containing the canonical persisted interaction."""

    user_id: str  # Registered user who owns the interaction.
    interaction_key: str  # DynamoDB sort key formatted as timestamp#movie_id#event_id.
    event_id: UUID  # Idempotent identifier generated at the API boundary.
    movie_id: str  # Referenced Movies.movie_id.
    interaction_type: InteractionType  # Recorded interaction category.
    interaction_action: InteractionWriteAction  # Recorded canonical action.
    interaction_value: float | None  # Optional value associated with the behavior.
    timestamp: datetime  # UTC behavior timestamp.
    session_id: str  # Session that produced the interaction.


class UserMovieRatingResponse(BaseModel):
    """Latest rating submitted by the authenticated user for one movie."""

    movie_id: str  # Referenced Movies.movie_id.
    rating: float | None = Field(default=None, ge=0.5, le=5.0)


class UserMovieReactionResponse(BaseModel):
    """Latest reaction submitted by the authenticated user for one movie."""

    movie_id: str  # Referenced Movies.movie_id.
    reaction: Literal["like", "dislike"] | None = None
