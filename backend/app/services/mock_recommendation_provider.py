from typing import List, Optional

from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.recommendation_provider import RecommendationProvider


class RecommendationMovie(MovieResponse):
    """Movie payload enriched with a recommendation score for the API contract."""

    score: Optional[float] = None


class MockRecommendationProvider(RecommendationProvider):
    """Temporary mock provider that simulates future ML inference."""

    def __init__(self, repository: Optional[InMemoryMovieRepository] = None) -> None:
        self._repository = repository or InMemoryMovieRepository()

    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        movies = self._repository.get_all()
        scores = [8.9, 8.4, 7.9]
        return [
            RecommendationMovie(
                id=movie.id,
                title=movie.title,
                genre=movie.genre,
                year=movie.year,
                rating=movie.rating,
                description=movie.description,
                image_url=movie.image_url,
                score=scores[index] if index < len(scores) else None,
            )
            for index, movie in enumerate(movies)
        ]
