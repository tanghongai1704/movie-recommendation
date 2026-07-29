"""Typed contract used by the deployed recommendation inference engine."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

SageMakerScenario = Literal[
    "guest",
    "onboarding_user",
    "returning_user",
]
SageMakerEventType = Literal[
    "click",
    "watch",
    "complete",
    "like",
    "dislike",
    "rating",
    "share",
    "comment",
]


class SageMakerInteraction(BaseModel):
    """One JSON-safe interaction accepted by RecommendationEngine."""

    model_config = ConfigDict(extra="forbid")

    movie_id: int
    event_type: SageMakerEventType
    value: float | str | None = None
    timestamp: str | None = None


class SageMakerRecommendationRequest(BaseModel):
    """Exact ``RecommendationEngine.recommend`` request contract."""

    model_config = ConfigDict(extra="forbid")

    user_id: int | None
    scenario_hint: SageMakerScenario
    onboarding_completed: bool
    valid_interaction_count_90d: int = Field(ge=0)
    selected_movie_ids: list[int] = Field(default_factory=list)
    selected_genres: list[str] = Field(default_factory=list)
    recent_interactions: list[SageMakerInteraction] = Field(
        default_factory=list,
        max_length=50,
    )
    exclude_movie_ids: list[int] = Field(default_factory=list)
    limit: int = Field(ge=1, le=50)


class SageMakerRecommendationResult(BaseModel):
    """One ranked movie reference returned by the inference engine."""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    movie_id: str = Field(min_length=1)
    score: float
    reason_code: str = Field(min_length=1)
    reason_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("movie_id", mode="before")
    @classmethod
    def normalize_movie_id(cls, value: Any) -> str:
        if value is None or isinstance(value, bool):
            raise ValueError("movie_id must be a non-empty identifier")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("movie_id must be a non-empty identifier")
        return normalized


class SageMakerEndpointResponse(BaseModel):
    """Native response emitted by ``RecommendationEngine.to_dict``."""

    model_config = ConfigDict(extra="ignore")

    model_name: str | None = None
    model_version: str | None = None
    scenario_applied: SageMakerScenario | None = None
    recommendation_type: str | None = None
    fallback_used: bool | None = None
    fallback_level: str | None = None
    generated_at: str | None = None
    artifact_versions: dict[str, str] = Field(default_factory=dict)
    recommendations: list[SageMakerRecommendationResult]


class SageMakerRecommendationResponse(BaseModel):
    """Normalized provider result independent of endpoint response variants."""

    model_config = ConfigDict(extra="forbid")

    scenario: SageMakerScenario
    model_version: str = Field(min_length=1)
    items: list[SageMakerRecommendationResult] = Field(min_length=1)
