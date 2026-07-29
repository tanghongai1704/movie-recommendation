from typing import Optional

from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.services.popular_movie_service import PopularMovieService
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService


class MovieService:
    def __init__(
        self,
        repository: MovieRepository,
        recommendation_service: Optional[RecommendationService] = None,
        popular_movie_service: Optional[PopularMovieService] = None,
    ) -> None:
        self._repository = repository
        self._recommendation_service = recommendation_service
        self._popular_movie_service = popular_movie_service

    def get_all_movies(self, limit: int = 24) -> list[MovieResponse]:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if self._popular_movie_service is not None:
            return self._popular_movie_service.get_movies(limit=limit)
        return [
            MovieResponse.model_validate(movie.model_dump())
            for movie in self._repository.list_all(limit=limit)
        ]

    def get_movie_by_id(self, movie_id: str) -> Optional[MovieResponse]:
        movie = self._repository.get(movie_id)
        return (
            MovieResponse.model_validate(movie.model_dump())
            if movie is not None
            else None
        )

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        if user_id is None:
            return self.get_all_movies(limit=10)
        if self._recommendation_service is None:
            return self.get_all_movies()
        return self._recommendation_service.get_recommendations(user_id=user_id)

    def get_recommendation_payload(
        self,
        user_id: str,
        limit: int = 10,
    ) -> RecommendationResponse:
        if self._recommendation_service is None:
            raise ValueError("recommendation service is not configured")
        return self._recommendation_service.get_recommendation_payload(
            user_id=user_id,
            limit=limit,
        )
