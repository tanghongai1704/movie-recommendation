from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.movie import MovieResponse
from app.services.movie_service import MovieService
from app.repositories.movie_repository import InMemoryMovieRepository

router = APIRouter()
security = HTTPBearer()

movie_service = MovieService(InMemoryMovieRepository())


def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not token.startswith("dummy-token-for-"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


@router.get("/movies", response_model=List[MovieResponse])
def list_movies(token: str = Depends(get_current_token)) -> List[MovieResponse]:
    return movie_service.get_all_movies()


@router.get("/movie/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, token: str = Depends(get_current_token)) -> MovieResponse:
    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return movie
