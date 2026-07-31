from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


MISSING_OVERVIEW_TEXT = "Overview unavailable."


class Movie(BaseModel):
    """Canonical movie metadata stored in the Movies table."""

    model_config = ConfigDict(extra="forbid")

    movie_id: str = Field(min_length=1)  # Stable Movies partition key used by every cross-table reference.
    title: str = Field(min_length=1)  # Display title of the movie.
    release_year: int | None = Field(ge=1800)  # Calendar year of release when the source provides it.
    genres: list[str]  # Normalized genre names used for browsing and onboarding.
    overview: str  # Long-form synopsis shown in catalog and detail views.
    poster_path: str | None  # Poster asset path or URL when artwork is available.
    vote_average: float = Field(ge=0.0, le=10.0)  # Aggregate audience vote average from the metadata source.
    vote_count: int = Field(ge=0)  # Number of votes contributing to vote_average.
    popularity: float = Field(ge=0.0)  # Source popularity signal used for catalog ranking.
    runtime: int | None = Field(gt=0)  # Runtime in minutes when known.
    original_language: str = Field(min_length=1)  # Original language code supplied by the metadata source.
    companies: list[str]  # Production company names embedded with movie metadata.
    countries: list[str]  # Production country names embedded with movie metadata.
    actors: list[str]  # Actor names embedded for display and feature generation.
    directors: list[str]  # Director names embedded for display and feature generation.

    @field_validator("overview", mode="before")
    @classmethod
    def normalize_missing_overview(cls, value: Any) -> Any:
        """Keep the API string contract when deployed records contain null."""

        return MISSING_OVERVIEW_TEXT if value is None else value
