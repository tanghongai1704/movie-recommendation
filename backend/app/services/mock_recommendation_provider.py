from typing import List, Optional

from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.recommendation_provider import RecommendationProvider


class MockRecommendationProvider(RecommendationProvider):
    """Temporary mock provider that simulates future ML inference."""

    def __init__(self, repository: Optional[InMemoryMovieRepository] = None) -> None:
        self._repository = repository or InMemoryMovieRepository()

    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        return self._repository.get_all()
