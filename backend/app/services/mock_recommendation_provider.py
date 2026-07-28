from typing import Optional

from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.recommendation_provider import RecommendationProvider


class RecommendationMovie(MovieResponse):
    """Movie payload enriched with a recommendation score for the API contract."""

    score: Optional[float] = None
    reason_code: Optional[str] = None


class MockRecommendationProvider(RecommendationProvider):
    """Temporary mock provider that simulates future ML inference."""

    def __init__(self, repository: Optional[InMemoryMovieRepository] = None) -> None:
        self._repository = repository or InMemoryMovieRepository()

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        movies = self._repository.list_all()
        scores = [8.9, 8.4, 7.9]
        return [
            RecommendationMovie(
                **movie.model_dump(),
                score=scores[index] if index < len(scores) else None,
                reason_code="mock_rank",
            )
            for index, movie in enumerate(movies)
        ]
