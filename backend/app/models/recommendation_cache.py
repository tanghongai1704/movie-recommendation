from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCacheItem(BaseModel):
    """One provider-ranked movie reference stored inside a cache entry."""

    model_config = ConfigDict(extra="forbid")

    movie_id: str = Field(min_length=1)  # Reference to Movies.movie_id; metadata is never duplicated here.
    score: float  # Provider ranking score used to preserve recommendation order.
    reason_code: str = Field(min_length=1)  # Stable explanation code suitable for API and analytics use.


class RecommendationCache(BaseModel):
    """Canonical recommendation result stored in RecommendationCache."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)  # Partition key identifying the recommendation recipient.
    scenario: str = Field(min_length=1)  # Sort key identifying context such as home or similar_movies.
    items: list[RecommendationCacheItem]  # Ordered provider results without movie metadata.
    model_version: str = Field(min_length=1)  # Version identifier of the provider/model that generated items.
    generated_at: datetime  # UTC time at which the recommendation set was generated.
    expire_at: int = Field(gt=0)  # Unix epoch seconds used for validity checks and DynamoDB TTL.
