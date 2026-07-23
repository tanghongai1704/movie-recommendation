from typing import List, Optional

from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse


class MovieService:
    def __init__(self, repository: MovieRepository) -> None:
        self._repository = repository

    def get_all_movies(self) -> List[MovieResponse]:
        return self._repository.get_all()

    def get_movie_by_id(self, movie_id: int) -> Optional[MovieResponse]:
        return self._repository.get_by_id(movie_id)
