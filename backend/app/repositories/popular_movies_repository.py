from typing import Any, Optional

from app.models.popular_movie import PopularMovie
from app.repositories.dynamodb_base import BaseDynamoDBRepository


class PopularMoviesRepository(BaseDynamoDBRepository):
    """CRUD persistence for the PopularMovies table."""

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

    def create(self, popular_movies: PopularMovie) -> PopularMovie:
        return self._create(popular_movies, partition_key="list_id")

    def get(self, list_id: str) -> Optional[PopularMovie]:
        return self._get(
            key={"list_id": list_id},
            model_type=PopularMovie,
        )

    def list_all(self) -> list[PopularMovie]:
        return self._scan_all(model_type=PopularMovie)

    def update(self, popular_movies: PopularMovie) -> PopularMovie:
        return self._update(popular_movies, partition_key="list_id")

    def delete(self, list_id: str) -> bool:
        return self._delete(key={"list_id": list_id})
