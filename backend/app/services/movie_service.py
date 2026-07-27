from typing import List, Optional

from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_provider import RecommendationProvider


class MovieService:
    def __init__(
        self,
        repository: MovieRepository,
        recommendation_provider: Optional[RecommendationProvider] = None,
    ) -> None:
        self._repository = repository
        self._recommendation_provider = recommendation_provider

    def get_all_movies(self) -> List[MovieResponse]:
        return self._repository.get_all()

    def get_movie_by_id(self, movie_id: int) -> Optional[MovieResponse]:
        return self._repository.get_by_id(movie_id)

    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        if self._recommendation_provider is None:
            return self.get_all_movies()
        return self._recommendation_provider.get_recommendations(user_id=user_id)

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
