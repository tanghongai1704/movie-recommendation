from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PopularMovie(BaseModel):
    """Canonical ranked list stored in the PopularMovies table."""

    model_config = ConfigDict(extra="forbid")

    list_id: str = Field(min_length=1)  # Stable partition key identifying one generated ranking list.
    ranking_type: str = Field(min_length=1)  # Ranking strategy, such as global or genre popularity.
    genre: str | None  # Optional genre scope for genre-specific ranking lists.
    movie_ids: list[str]  # Ordered references to Movies.movie_id without metadata copies.
    scores: list[float]  # Scores aligned by position with movie_ids.
    generated_at: datetime  # UTC time at which the ranking list was generated.

    @model_validator(mode="after")
    def validate_ranked_items(self) -> "PopularMovie":
        """Require one score for every ranked movie reference."""

        if len(self.movie_ids) != len(self.scores):
            raise ValueError("movie_ids and scores must have the same length")
        return self
