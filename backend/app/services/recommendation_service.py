from typing import List, Optional

from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_provider import RecommendationProvider


class RecommendationService:
    """Builds recommendation payloads using a provider implementation."""

    def __init__(self, provider: RecommendationProvider) -> None:
        self._provider = provider

    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        return self._provider.get_recommendations(user_id=user_id)

    def get_recommendation_payload(self, user_id: int, limit: int = 10) -> RecommendationResponse:
        if user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        items = self.get_recommendations(user_id=user_id)[:limit]
        return RecommendationResponse(
            user_id=user_id,
            recommendations=[
                {
                    "movie_id": item.id,
                    "title": item.title,
                    "score": getattr(item, "score", None),
                }
                for item in items
            ],
        )
