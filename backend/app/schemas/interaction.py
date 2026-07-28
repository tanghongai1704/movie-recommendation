from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.user_interaction import InteractionAction, InteractionType

ALLOWED_ACTIONS = {
    InteractionType.CLICK: {InteractionAction.OPEN_DETAIL},
    InteractionType.WATCH: {
        InteractionAction.WATCH_START,
        InteractionAction.WATCH_PROGRESS,
        InteractionAction.WATCH_COMPLETE,
    },
    InteractionType.RATING: {InteractionAction.RATING_SUBMIT},
    InteractionType.REACTION: {
        InteractionAction.REACTION_LIKE,
        InteractionAction.REACTION_DISLIKE,
    },
    InteractionType.SHARE: {
        InteractionAction.SHARE_NATIVE,
        InteractionAction.SHARE_COPY_LINK,
    },
}


class InteractionCreate(BaseModel):
    """Request DTO for recording a canonical interaction."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    interaction_type: InteractionType = Field(
        validation_alias=AliasChoices("interaction_type", "event_type"),
    )  # Canonical behavior category; event_type remains an input-only migration alias.
    interaction_action: InteractionAction  # Concrete action within the behavior category.
    movie_id: str = Field(min_length=1, pattern=r"^[^#]+$")  # Canonical Movies.movie_id reference.
    interaction_value: float | None = Field(
        default=None,
        validation_alias=AliasChoices("interaction_value", "rating"),
    )  # Optional behavior value; rating remains an input-only migration alias.
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

        if self.interaction_type == InteractionType.RATING:
            if self.interaction_value is None:
                raise ValueError(
                    "interaction_value is required when interaction_type is 'rating'"
                )
            if not 0.5 <= self.interaction_value <= 5.0:
                raise ValueError("rating interaction_value must be between 0.5 and 5.0")
        if (
            self.interaction_type == InteractionType.WATCH
            and self.interaction_value is not None
            and self.interaction_value < 0
        ):
            raise ValueError("watch interaction_value must not be negative")
        return self


class InteractionResponse(BaseModel):
    """API response containing the canonical persisted interaction."""

    user_id: str  # Registered user who owns the interaction.
    interaction_key: str  # DynamoDB sort key formatted as timestamp#movie_id#event_id.
    event_id: UUID  # Idempotent identifier generated at the API boundary.
    movie_id: str  # Referenced Movies.movie_id.
    interaction_type: InteractionType  # Recorded interaction category.
    interaction_action: InteractionAction  # Recorded action within the category.
    interaction_value: float | None  # Optional value associated with the behavior.
    timestamp: datetime  # UTC behavior timestamp.
    session_id: str  # Session that produced the interaction.
