from datetime import datetime

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PopularMovie(BaseModel):
    """Canonical ranked list stored in the PopularMovies table."""

    model_config = ConfigDict(extra="forbid")

    list_id: str = Field(min_length=1)  # Stable partition key identifying one generated ranking list.
    ranking_type: str | None = Field(default=None, min_length=1)  # Ranking strategy when present in the deployed record.
    genre: str | None  # Optional genre scope for genre-specific ranking lists.
    movie_ids: list[str]  # Ordered references to Movies.movie_id without metadata copies.
    scores: list[float]  # Scores aligned by position with movie_ids.
    generated_at: datetime  # UTC time at which the ranking list was generated.

    @model_validator(mode="before")
    @classmethod
    def normalize_deployed_movie_ids(cls, value: Any) -> Any:
        """Normalize legacy DynamoDB Number references without rewriting data."""

        if not isinstance(value, dict):
            return value
        record = dict(value)
        movie_ids = record.get("movie_ids")
        if isinstance(movie_ids, list):
            record["movie_ids"] = [
                str(int(movie_id))
                if isinstance(movie_id, Decimal)
                and movie_id == movie_id.to_integral_value()
                else str(movie_id)
                for movie_id in movie_ids
            ]
        return record

    @model_validator(mode="after")
    def validate_ranked_items(self) -> "PopularMovie":
        """Require one score for every ranked movie reference."""

        if len(self.movie_ids) != len(self.scores):
            raise ValueError("movie_ids and scores must have the same length")
        return self
