from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.movie import MovieResponse


class MovieRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[MovieResponse]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, movie_id: int) -> Optional[MovieResponse]:
        raise NotImplementedError


class InMemoryMovieRepository(MovieRepository):
    def __init__(self) -> None:
        self._movies: List[MovieResponse] = [
            MovieResponse(
                id=1,
                title="Midnight Horizon",
                genre="Sci-Fi Thriller",
                year=2025,
                rating=8.9,
                description="A brilliant pilot and a rogue AI race through a collapsing city.",
                image_url="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1400&q=80",
            ),
            MovieResponse(
                id=2,
                title="Shadow Protocol",
                genre="Cyberpunk",
                year=2024,
                rating=8.4,
                description="A covert operative uncovers a citywide surveillance conspiracy.",
                image_url="https://images.unsplash.com/photo-1517602302552-471fe67acf66?auto=format&fit=crop&w=800&q=80",
            ),
            MovieResponse(
                id=3,
                title="Neon Coast",
                genre="Drama",
                year=2023,
                rating=7.9,
                description="A stranded musician faces the sea and the truth about her past.",
                image_url="https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=800&q=80",
            ),
        ]

    def get_all(self) -> List[MovieResponse]:
        return self._movies

    def get_by_id(self, movie_id: int) -> Optional[MovieResponse]:
        return next((movie for movie in self._movies if movie.id == movie_id), None)
