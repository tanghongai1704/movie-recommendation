from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService
from app.services.dynamodb.user_activity_repository import RecommendationCacheRepository

router = APIRouter()
security = HTTPBearer()

recommendation_service = RecommendationService(
    provider=MockRecommendationProvider(),
    cache=RecommendationCacheRepository(
        table_name=settings.AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE,
        region_name=settings.AWS_REGION,
    ),
    cache_ttl_seconds=settings.RECOMMENDATION_CACHE_TTL_SECONDS,
)
movie_service = MovieService(
    repository=InMemoryMovieRepository(),
    recommendation_service=recommendation_service,
)


def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not token.startswith(settings.AUTH_TOKEN_PREFIX):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


@router.get("/movies", response_model=List[MovieResponse])
def list_movies(token: str = Depends(get_current_token)) -> List[MovieResponse]:
    return movie_service.get_recommendations(user_id=1)


@router.get("/recommend/{user_id}", response_model=RecommendationResponse)
def get_recommendations(user_id: int, token: str = Depends(get_current_token)) -> RecommendationResponse:
    try:
        return movie_service.get_recommendation_payload(user_id=user_id, limit=10)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/movie/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, token: str = Depends(get_current_token)) -> MovieResponse:
    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return movie
