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
        batch_reader: Any | None = None,
        batch_max_attempts: int = 3,
    ) -> None:
        super().__init__(
            table_name=table_name,
            region_name=region_name,
            table=table,
        )
        if batch_max_attempts <= 0:
            raise ValueError("batch_max_attempts must be a positive integer")
        self._batch_reader = batch_reader
        self._batch_max_attempts = batch_max_attempts

    def create(self, movie: Movie) -> Movie:
        return self._create(movie, partition_key="movie_id")

    def get(self, movie_id: str) -> Optional[Movie]:
        return self._get(
            key={"movie_id": movie_id},
            model_type=Movie,
        )

    def list_all(self, limit: int | None = None) -> list[Movie]:
        return self._scan_all(model_type=Movie, limit=limit)

    def get_many(self, movie_ids: list[str]) -> list[Movie]:
        """Resolve movie references in order using DynamoDB BatchGetItem."""

        if not movie_ids:
            return []
        if self._batch_reader is None:
            # Repository unit tests may inject only a table double. Production
            # composition always injects the DynamoDB service resource.
            return super().get_many(movie_ids)

        unique_ids = list(dict.fromkeys(movie_ids))
        resolved: dict[str, Movie] = {}
        try:
            for offset in range(0, len(unique_ids), 100):
                pending = {
                    self.table_name: {
                        "Keys": [
                            {"movie_id": movie_id}
                            for movie_id in unique_ids[offset : offset + 100]
                        ]
                    }
                }
                for _attempt in range(self._batch_max_attempts):
                    response = self._batch_reader.batch_get_item(
                        RequestItems=pending
                    )
                    for item in response.get("Responses", {}).get(
                        self.table_name,
                        [],
                    ):
                        movie = Movie.model_validate(item)
                        resolved[movie.movie_id] = movie
                    pending = response.get("UnprocessedKeys", {})
                    if not pending.get(self.table_name, {}).get("Keys"):
                        break
                else:
                    raise RuntimeError(
                        "DynamoDB did not process all movie keys after retries"
                    )
        except Exception as exc:
            self._handle_error(exc)

        return [
            resolved[movie_id]
            for movie_id in movie_ids
            if movie_id in resolved
        ]

    def update(self, movie: Movie) -> Movie:
        return self._update(movie, partition_key="movie_id")

    def delete(self, movie_id: str) -> bool:
        return self._delete(key={"movie_id": movie_id})
