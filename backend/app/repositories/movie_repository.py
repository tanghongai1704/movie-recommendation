from abc import ABC, abstractmethod
from typing import Optional

from app.models.movie import Movie


class MovieRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Movie]:
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


class InMemoryMovieRepository(MovieRepository):
    def __init__(self) -> None:
        self._movies: list[Movie] = [
            Movie(
                movie_id="1",
                title="Midnight Horizon",
                release_year=2025,
                genres=["Science Fiction", "Thriller"],
                overview="A brilliant pilot and a rogue AI race through a collapsing city.",
                poster_path="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1400&q=80",
                vote_average=8.9,
                vote_count=12_400,
                popularity=94.1,
                runtime=132,
                original_language="en",
                companies=["Northstar Pictures"],
                countries=["United States"],
                actors=["Avery Chen", "Maya Stone"],
                directors=["Jordan Vale"],
            ),
            Movie(
                movie_id="2",
                title="Shadow Protocol",
                release_year=2024,
                genres=["Science Fiction", "Action"],
                overview="A covert operative uncovers a citywide surveillance conspiracy.",
                poster_path="https://images.unsplash.com/photo-1517602302552-471fe67acf66?auto=format&fit=crop&w=800&q=80",
                vote_average=8.4,
                vote_count=9_750,
                popularity=88.6,
                runtime=118,
                original_language="en",
                companies=["Vector House"],
                countries=["United Kingdom"],
                actors=["Noah Hart", "Lina Park"],
                directors=["Sam Rivera"],
            ),
            Movie(
                movie_id="3",
                title="Neon Coast",
                release_year=2023,
                genres=["Drama"],
                overview="A stranded musician faces the sea and the truth about her past.",
                poster_path="https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=800&q=80",
                vote_average=7.9,
                vote_count=6_220,
                popularity=76.8,
                runtime=105,
                original_language="en",
                companies=["Blue Current Films"],
                countries=["Australia"],
                actors=["Iris Cole", "Theo Bennett"],
                directors=["Riley Brooks"],
            ),
        ]

    def list_all(self) -> list[Movie]:
        return self._movies

    def get(self, movie_id: str) -> Optional[Movie]:
        return next(
            (movie for movie in self._movies if movie.movie_id == movie_id),
            None,
        )
