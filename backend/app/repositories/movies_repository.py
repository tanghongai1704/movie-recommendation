from typing import Any, Optional

from app.models.movie import Movie
from app.repositories.dynamodb_base import BaseDynamoDBRepository
from app.repositories.movie_repository import MovieRepository


class MoviesRepository(BaseDynamoDBRepository, MovieRepository):
    """CRUD persistence for the Movies table."""

    def __init__(
        self,
        *,
        table_name: str,
        region_name: str,
        table: Any | None = None,
    ) -> None:
        super().__init__(
            table_name=table_name,
            region_name=region_name,
            table=table,
        )

    def create(self, movie: Movie) -> Movie:
        return self._create(movie, partition_key="movie_id")

    def get(self, movie_id: str) -> Optional[Movie]:
        return self._get(
            key={"movie_id": movie_id},
            model_type=Movie,
        )

    def list_all(self) -> list[Movie]:
        return self._scan_all(model_type=Movie)

    def update(self, movie: Movie) -> Movie:
        return self._update(movie, partition_key="movie_id")

    def delete(self, movie_id: str) -> bool:
        return self._delete(key={"movie_id": movie_id})
