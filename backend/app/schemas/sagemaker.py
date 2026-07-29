from pydantic import BaseModel, ConfigDict, Field


class SageMakerRecommendationRequest(BaseModel):
    """Versioned JSON payload prepared for the future inference container."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    limit: int = Field(ge=1, le=100)


class SageMakerRecommendationResult(BaseModel):
    """One ranked movie reference returned by the inference container."""

    model_config = ConfigDict(extra="forbid")

    movie_id: str = Field(min_length=1)
    score: float
    reason_code: str = Field(min_length=1)


class SageMakerRecommendationResponse(BaseModel):
    """Expected response contract for a deployed SageMaker endpoint."""

    model_config = ConfigDict(extra="forbid")

    model_version: str = Field(min_length=1)
    items: list[SageMakerRecommendationResult]
