from abc import ABC, abstractmethod
from typing import Optional

from app.models.movie import Movie


class MovieRepository(ABC):
    @abstractmethod
    def list_all(self, limit: int | None = None) -> list[Movie]:
        raise NotImplementedError

    @abstractmethod
    def get(self, movie_id: str) -> Optional[Movie]:
        raise NotImplementedError

    def get_many(self, movie_ids: list[str]) -> list[Movie]:
        """Resolve movie IDs in caller-provided order."""

        movies: list[Movie] = []
        for movie_id in movie_ids:
            movie = self.get(movie_id)
            if movie is not None:
                movies.append(movie)
        return movies
