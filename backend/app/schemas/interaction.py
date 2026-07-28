from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.user_interaction import InteractionType


class InteractionCreate(BaseModel):
    """Request DTO for recording a canonical interaction."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    interaction_type: InteractionType = Field(
        validation_alias=AliasChoices("interaction_type", "event_type"),
    )  # Canonical behavior category; event_type remains an input-only migration alias.
    movie_id: str  # Canonical Movies.movie_id reference.
    interaction_value: float | None = Field(
        default=None,
        validation_alias=AliasChoices("interaction_value", "rating"),
    )  # Optional behavior value; rating remains an input-only migration alias.
    session_id: str = "legacy-session"  # Client session identifier; default preserves legacy clients.

    @field_validator("movie_id", mode="before")
    @classmethod
    def normalize_movie_id(cls, value: object) -> str:
        """Normalize legacy numeric identifiers to the canonical string type."""

        return str(value)

    @model_validator(mode="after")
    def validate_rating_event(self) -> "InteractionCreate":
        if self.interaction_type == InteractionType.RATING:
            if self.interaction_value is None:
                raise ValueError(
                    "interaction_value is required when interaction_type is 'rating'"
                )
            if not 0.5 <= self.interaction_value <= 5.0:
                raise ValueError("rating interaction_value must be between 0.5 and 5.0")
        return self


class InteractionResponse(BaseModel):
    """API response containing the canonical persisted interaction."""

    user_id: str  # Registered user who owns the interaction.
    interaction_key: str  # DynamoDB sort key formatted as timestamp#movie_id.
    movie_id: str  # Referenced Movies.movie_id.
    interaction_type: InteractionType  # Recorded click, watch, or rating category.
    interaction_value: float | None  # Optional value associated with the behavior.
    timestamp: datetime  # UTC behavior timestamp.
    session_id: str  # Session that produced the interaction.
