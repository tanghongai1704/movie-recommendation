from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class InteractionEventType(str, Enum):
    CLICK = "click"
    WATCH = "watch"
    RATING = "rating"


class InteractionCreate(BaseModel):
    event_type: InteractionEventType
    movie_id: int = Field(gt=0)
    rating: Optional[float] = Field(default=None, ge=0.5, le=5.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rating_event(self) -> "InteractionCreate":
        if self.event_type == InteractionEventType.RATING and self.rating is None:
            raise ValueError("rating is required when event_type is 'rating'")
        return self


class InteractionResponse(BaseModel):
    event_id: str
    user_id: int
    event_type: InteractionEventType
    movie_id: int
    rating: Optional[float] = None
    created_at: str
