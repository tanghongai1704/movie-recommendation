from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_completed_onboarding
from app.core.config import settings
from app.models.user import User
from app.repositories.movie_repository import InMemoryMovieRepository
from app.repositories.recommendation_cache_repository import (
    RecommendationCacheRepository,
)
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService

router = APIRouter()

movie_repository = InMemoryMovieRepository()
recommendation_service = RecommendationService(
    provider=MockRecommendationProvider(repository=movie_repository),
    cache=RecommendationCacheRepository(
        table_name=settings.AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE,
        region_name=settings.AWS_REGION,
    ),
    movie_repository=movie_repository,
    cache_ttl_seconds=settings.RECOMMENDATION_CACHE_TTL_SECONDS,
)
movie_service = MovieService(
    repository=movie_repository,
    recommendation_service=recommendation_service,
)


@router.get("/movies", response_model=list[MovieResponse])
def list_movies() -> list[MovieResponse]:
    """Public movie catalog available to guests and registered users."""

    return movie_service.get_all_movies()


@router.get("/recommend/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    user: User = Depends(require_completed_onboarding),
) -> RecommendationResponse:
    if user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recommendations can only be requested for the current user",
        )
    try:
        return movie_service.get_recommendation_payload(
            user_id=user.user_id,
            limit=10,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/movie/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str) -> MovieResponse:
    """Public movie detail available to guests and registered users."""

    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )
    return movie
