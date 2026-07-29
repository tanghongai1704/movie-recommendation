from app.repositories.movie_repository import MovieRepository
from app.repositories.popular_movies_repository import PopularMoviesRepository
from app.schemas.movie import MovieResponse


class PopularMoviesNotFoundError(Exception):
    """Raised when the configured deployed ranking list does not exist."""


class PopularMovieService:
    """Enrich one DynamoDB PopularMovies ranking with Movies metadata."""

    def __init__(
        self,
        *,
        popular_movies: PopularMoviesRepository,
        movies: MovieRepository,
        list_id: str,
    ) -> None:
        if not list_id.strip():
            raise ValueError("popular list_id must not be empty")
        self._popular_movies = popular_movies
        self._movies = movies
        self._list_id = list_id

    def get_movies(self, *, limit: int) -> list[MovieResponse]:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        ranking = self._popular_movies.get(self._list_id)
        if ranking is None:
            raise PopularMoviesNotFoundError(
                "The configured PopularMovies list does not exist"
            )
        return [
            MovieResponse.model_validate(movie.model_dump())
            for movie in self._movies.get_many(ranking.movie_ids[:limit])
        ]
