from datetime import datetime, timezone
from time import time
from typing import Callable, Optional, Protocol

from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.services.recommendation_provider import RecommendationProvider


class RecommendationCacheStore(Protocol):
    """Persistence boundary used by RecommendationService."""

    def get(
        self,
        user_id: str,
        scenario: str,
    ) -> Optional[RecommendationCache]:
        ...

    def upsert(self, item: RecommendationCache) -> RecommendationCache:
        ...


class CachedRecommendationMovie(MovieResponse):
    """Movie metadata enriched with fields stored in RecommendationCache.items."""

    score: float  # Ranking score restored from the normalized cache item.
    reason_code: str  # Explanation code restored from the normalized cache item.


class RecommendationService:
    """Returns cached recommendations or populates the cache from a provider."""

    def __init__(
        self,
        provider: RecommendationProvider,
        cache: RecommendationCacheStore,
        movie_repository: MovieRepository,
        *,
        cache_ttl_seconds: int,
        scenario: str,
        model_version: str,
        clock: Callable[[], float] = time,
    ) -> None:
        if cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be a positive integer")

        self._provider = provider
        self._cache = cache
        self._movie_repository = movie_repository
        self._cache_ttl_seconds = cache_ttl_seconds
        self._scenario = scenario
        self._model_version = model_version
        self._clock = clock

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        if user_id is None:
            return self._provider.get_recommendations(user_id=None)
        if not user_id:
            raise ValueError("user_id must not be empty")

        cached_movies = self._get_valid_cached_movies(user_id)
        if cached_movies is not None:
            return cached_movies

        movies = self._provider.get_recommendations(user_id=user_id)
        self._save_to_cache(user_id=user_id, movies=movies)
        return movies

    def get_recommendation_payload(
        self,
        user_id: str,
        limit: int = 10,
    ) -> RecommendationResponse:
        if not user_id:
            raise ValueError("user_id must not be empty")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        movies = self.get_recommendations(user_id=user_id)[:limit]
        return RecommendationResponse(
            user_id=user_id,
            recommendations=[
                RecommendationItem.model_validate(
                    movie.model_dump(),
                )
                for movie in movies
            ],
        )

    def _get_valid_cached_movies(
        self,
        user_id: str,
    ) -> Optional[list[CachedRecommendationMovie]]:
        cached = self._cache.get(user_id=user_id, scenario=self._scenario)
        if cached is None or cached.expire_at <= self._clock():
            return None

        movies: list[CachedRecommendationMovie] = []
        for item in cached.items:
            movie = self._movie_repository.get(item.movie_id)
            if movie is None:
                return None
            movies.append(
                CachedRecommendationMovie(
                    **movie.model_dump(),
                    score=item.score,
                    reason_code=item.reason_code,
                )
            )
        return movies

    def _save_to_cache(
        self,
        user_id: str,
        movies: list[MovieResponse],
    ) -> None:
        now = self._clock()
        items = [
            RecommendationCacheItem(
                movie_id=movie.movie_id,
                score=float(getattr(movie, "score", 0.0) or 0.0),
                reason_code=str(
                    getattr(movie, "reason_code", None) or "provider_default"
                ),
            )
            for movie in movies
        ]
        self._cache.upsert(
            RecommendationCache(
                user_id=user_id,
                scenario=self._scenario,
                items=items,
                model_version=self._model_version,
                generated_at=datetime.fromtimestamp(now, tz=timezone.utc),
                expire_at=int(now) + self._cache_ttl_seconds,
            )
        )
