from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class StoredRecommendationCache(BaseModel):
    """Read-compatible cache record for canonical and deployed legacy items."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    items: list[RecommendationCacheItem]
    model_version: str = Field(min_length=1)
    generated_at: datetime
    expire_at: int = Field(gt=0)
    source_provider: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_deployed_record(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        record = dict(value)
        provider = record.get("provider")
        record["source_provider"] = provider
        if record.get("items") is None:
            details_by_id: dict[str, dict[str, Any]] = {}
            for detail in record.get("movies") or []:
                if not isinstance(detail, dict):
                    continue
                movie_id = detail.get("movie_id", detail.get("id"))
                if movie_id is not None:
                    details_by_id[_string_id(movie_id)] = detail

            record["items"] = [
                {
                    "movie_id": movie_id,
                    "score": float(
                        details_by_id.get(movie_id, {}).get("score", 0.0)
                    ),
                    "reason_code": "legacy_cache",
                }
                for movie_id in (
                    _string_id(item)
                    for item in record.get("movie_ids") or []
                )
            ]
        if record.get("model_version") is None:
            record["model_version"] = str(provider or "legacy")
        if record.get("generated_at") is None:
            record["generated_at"] = record.get("cached_at")
        if record.get("expire_at") is None:
            record["expire_at"] = record.get("expires_at")
        return record

    def to_canonical(self) -> RecommendationCache:
        return RecommendationCache.model_validate(
            self.model_dump(exclude={"source_provider"})
        )


def _string_id(value: Any) -> str:
    if isinstance(value, Decimal) and value == value.to_integral_value():
        return str(int(value))
    return str(value)
