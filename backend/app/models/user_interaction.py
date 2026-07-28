from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class InteractionType(str, Enum):
    """Supported user behavior events."""

    CLICK = "click"
    WATCH = "watch"
    RATING = "rating"


class UserInteraction(BaseModel):
    """Canonical behavior record stored in the UserInteractions table."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)  # Partition key identifying the registered user who acted.
    interaction_key: str = Field(min_length=3)  # Sort key formatted as timestamp#movie_id.
    movie_id: str = Field(min_length=1)  # Reference to the interacted Movies.movie_id.
    interaction_type: InteractionType  # Behavior category: click, watch, or rating.
    interaction_value: float | None  # Optional numeric value, required for a rating.
    timestamp: datetime  # UTC time at which the behavior occurred.
    session_id: str = Field(min_length=1)  # Client session identifier used to group related behavior.
