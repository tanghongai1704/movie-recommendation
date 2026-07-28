from typing import Optional

from pydantic import BaseModel

from app.schemas.movie import MovieResponse


class RecommendationItem(MovieResponse):
    """Enriched recommendation returned by the API."""

    score: Optional[float] = None  # Provider ranking score for this movie.
    reason_code: Optional[str] = None  # Stable provider explanation code.


class RecommendationResponse(BaseModel):
    """Stable API envelope for personalized recommendations."""

    user_id: str  # Registered user for whom recommendations were generated.
    recommendations: list[RecommendationItem]  # Ordered, metadata-enriched results.
