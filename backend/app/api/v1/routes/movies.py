from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.movie_service import MovieService
from app.repositories.movie_repository import InMemoryMovieRepository
from app.services.mock_recommendation_provider import MockRecommendationProvider
from ml.services.recommendation_service import RecommendationService, RecommendationServiceError

router = APIRouter()
security = HTTPBearer()

movie_service = MovieService(
    repository=InMemoryMovieRepository(),
    recommendation_provider=MockRecommendationProvider(),
)
ml_recommendation_service = RecommendationService()


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
        raw_recommendations = ml_recommendation_service.recommend(user_id=user_id, limit=10)
    except RecommendationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RecommendationResponse(
        user_id=user_id,
        recommendations=[
            {"movie_id": item["movie_id"], "title": item["title"], "score": item.get("score")}
            for item in raw_recommendations
        ],
    )


@router.get("/movie/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, token: str = Depends(get_current_token)) -> MovieResponse:
    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return movie
