from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import require_completed_onboarding
from app.container import movie_service
from app.models.user import User
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.popular_movie_service import PopularMoviesNotFoundError
from app.services.recommendation_provider import (
    RecommendationProviderResponseError,
    RecommendationProviderTimeoutError,
    RecommendationProviderUnavailableError,
)

router = APIRouter()


@router.get("/movies", response_model=list[MovieResponse])
def list_movies(
    limit: int = Query(default=24, ge=1, le=100),
) -> list[MovieResponse]:
    """Public movie catalog available to guests and registered users."""

    try:
        return movie_service.get_all_movies(limit=limit)
    except (DynamoDBRepositoryError, PopularMoviesNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load movies",
        ) from exc


@router.get("/recommend/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
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
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load recommendations",
        ) from exc
    except RecommendationProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalized recommendations are not available",
        ) from exc
    except RecommendationProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Recommendation model timed out",
        ) from exc
    except RecommendationProviderResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Recommendation model returned an invalid response",
        ) from exc


@router.get("/movie/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str) -> MovieResponse:
    """Public movie detail available to guests and registered users."""

    try:
        movie = movie_service.get_movie_by_id(movie_id)
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load movie",
        ) from exc
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )
    return movie
