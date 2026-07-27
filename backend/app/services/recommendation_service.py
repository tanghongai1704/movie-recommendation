from datetime import datetime, timezone
from time import time
from typing import Any, Callable, List, Optional, Protocol

from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_provider import RecommendationProvider


class RecommendationCache(Protocol):
    def get_item(self, user_id: Any, scenario: str) -> Optional[dict[str, Any]]:
        ...

    def put_item(self, item: dict[str, Any]) -> dict[str, Any]:
        ...


class CachedRecommendationMovie(MovieResponse):
    score: Optional[float] = None


class RecommendationService:
    """Returns cached recommendations or populates the cache from a provider."""

    def __init__(
        self,
        provider: RecommendationProvider,
        cache: RecommendationCache,
        *,
        cache_ttl_seconds: int = 300,
        scenario: str = "default",
        clock: Callable[[], float] = time,
    ) -> None:
        if cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be a positive integer")

        self._provider = provider
        self._cache = cache
        self._cache_ttl_seconds = cache_ttl_seconds
        self._scenario = scenario
        self._clock = clock

    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        if user_id is None:
            return self._provider.get_recommendations(user_id=None)
        if user_id <= 0:
            raise ValueError("user_id must be a positive integer")

        cached_movies = self._get_valid_cached_movies(user_id)
        if cached_movies is not None:
            return cached_movies

        movies = self._provider.get_recommendations(user_id=user_id)
        self._save_to_cache(user_id=user_id, movies=movies)
        return movies

    def get_recommendation_payload(self, user_id: int, limit: int = 10) -> RecommendationResponse:
        if user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        items = self.get_recommendations(user_id=user_id)[:limit]
        return RecommendationResponse(
            user_id=user_id,
            recommendations=[
                {
                    "movie_id": item.id,
                    "title": item.title,
                    "score": getattr(item, "score", None),
                }
                for item in items
            ],
        )

    def _get_valid_cached_movies(
        self,
        user_id: int,
    ) -> Optional[List[CachedRecommendationMovie]]:
        cached = self._cache.get_item(user_id=user_id, scenario=self._scenario)
        if not cached:
            return None

        try:
            expires_at = float(cached["expires_at"])
            movie_ids = [int(movie_id) for movie_id in cached["movie_ids"]]
            snapshots = cached["movies"]
            if not isinstance(snapshots, list):
                return None

            movies = [
                CachedRecommendationMovie.model_validate(snapshot)
                for snapshot in snapshots
            ]
        except (KeyError, TypeError, ValueError):
            return None

        if expires_at <= self._clock():
            return None
        if [movie.id for movie in movies] != movie_ids:
            return None
        return movies

    def _save_to_cache(self, user_id: int, movies: List[MovieResponse]) -> None:
        now = self._clock()
        expires_at = int(now) + self._cache_ttl_seconds
        cached_at = datetime.fromtimestamp(now, tz=timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )

        self._cache.put_item(
            {
                "user_id": str(user_id),
                "scenario": self._scenario,
                "movie_ids": [movie.id for movie in movies],
                "movies": [movie.model_dump(mode="json") for movie in movies],
                "cached_at": cached_at,
                "expires_at": expires_at,
                "provider": type(self._provider).__name__,
                "schema_version": 1,
            }
        )
