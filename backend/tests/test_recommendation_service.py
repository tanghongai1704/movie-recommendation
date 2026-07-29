import unittest
from typing import Optional

from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.models.movie import Movie
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationItem
from app.services.recommendation_provider import RecommendationProvider
from app.services.recommendation_service import RecommendationService


class TestRecommendationCache:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], RecommendationCache] = {}
        self.get_calls = 0
        self.put_calls = 0

    def get(
        self,
        user_id: str,
        scenario: str,
    ) -> Optional[RecommendationCache]:
        self.get_calls += 1
        return self.items.get((user_id, scenario))

    def upsert(self, item: RecommendationCache) -> RecommendationCache:
        self.put_calls += 1
        self.items[(item.user_id, item.scenario)] = item
        return item


class StaticMovieRepository(MovieRepository):
    def __init__(self) -> None:
        self.movies = [
            Movie(
                movie_id=str(index),
                title=title,
                release_year=2025,
                genres=["Drama"],
                overview="Test movie",
                poster_path="/poster.jpg",
                vote_average=8.0,
                vote_count=100,
                popularity=10.0,
                runtime=100,
                original_language="en",
                companies=["Studio"],
                countries=["Vietnam"],
                actors=["Actor"],
                directors=["Director"],
            )
            for index, title in enumerate(
                ("First movie", "Second movie", "Third movie"),
                start=1,
            )
        ]

    def list_all(self, limit: int | None = None) -> list[Movie]:
        return self.movies if limit is None else self.movies[:limit]

    def get(self, movie_id: str) -> Optional[Movie]:
        return next(
            (movie for movie in self.movies if movie.movie_id == movie_id),
            None,
        )

    def get_many(self, movie_ids: list[str]) -> list[Movie]:
        by_id = {movie.movie_id: movie for movie in self.movies}
        return [by_id[movie_id] for movie_id in movie_ids if movie_id in by_id]


class CountingRecommendationProvider(RecommendationProvider):
    def __init__(self, repository: StaticMovieRepository) -> None:
        self.calls = 0
        self._repository = repository

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        del user_id
        self.calls += 1
        return [
            RecommendationItem(
                **movie.model_dump(),
                score=score,
                reason_code="test_rank",
            )
            for movie, score in zip(
                self._repository.list_all(),
                (8.9, 8.4, 7.9),
                strict=True,
            )
        ]


class RecommendationServiceTests(unittest.TestCase):
    def make_dependencies(
        self,
    ) -> tuple[
        StaticMovieRepository,
        CountingRecommendationProvider,
        TestRecommendationCache,
    ]:
        repository = StaticMovieRepository()
        return (
            repository,
            CountingRecommendationProvider(repository),
            TestRecommendationCache(),
        )

    def make_service(
        self,
        repository: StaticMovieRepository,
        provider: CountingRecommendationProvider,
        cache: TestRecommendationCache,
        now: float = 1_000.0,
    ) -> RecommendationService:
        return RecommendationService(
            provider=provider,
            cache=cache,
            movie_repository=repository,
            cache_ttl_seconds=60,
            scenario="default",
            model_version="test-model-v1",
            clock=lambda: now,
        )

    def test_cache_miss_calls_provider_and_saves_canonical_items(self) -> None:
        repository, provider, cache = self.make_dependencies()
        service = self.make_service(repository, provider, cache)

        response = service.get_recommendation_payload(user_id="42", limit=2)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.get_calls, 1)
        self.assertEqual(cache.put_calls, 1)
        cached = cache.items[("42", "default")]
        self.assertEqual(
            [item.movie_id for item in cached.items],
            ["1", "2", "3"],
        )
        self.assertEqual(cached.model_version, "test-model-v1")
        self.assertEqual(cached.expire_at, 1_060)
        self.assertEqual(response.user_id, "42")
        self.assertEqual(
            [item.movie_id for item in response.recommendations],
            ["1", "2"],
        )

    def test_valid_cache_hit_enriches_metadata_without_provider_call(self) -> None:
        repository, provider, cache = self.make_dependencies()
        service = self.make_service(repository, provider, cache)
        first = service.get_recommendation_payload(user_id="42")

        second = service.get_recommendation_payload(user_id="42")

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual(second, first)
        self.assertEqual(second.recommendations[0].title, "First movie")
        self.assertEqual(second.recommendations[0].score, 8.9)

    def test_expired_cache_calls_provider_and_replaces_entry(self) -> None:
        repository, provider, cache = self.make_dependencies()
        service = self.make_service(repository, provider, cache, now=1_000.0)
        service.get_recommendations(user_id="7")
        cache.items[("7", "default")].expire_at = 999
        provider.calls = 0
        cache.put_calls = 0

        service.get_recommendations(user_id="7")

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual(cache.items[("7", "default")].expire_at, 1_060)

    def test_unresolvable_cache_item_calls_provider(self) -> None:
        repository, provider, cache = self.make_dependencies()
        service = self.make_service(repository, provider, cache)
        service.get_recommendations(user_id="9")
        cache.items[("9", "default")].items = [
            RecommendationCacheItem(
                movie_id="999",
                score=1.0,
                reason_code="test",
            )
        ]
        provider.calls = 0
        cache.put_calls = 0

        movies = service.get_recommendations(user_id="9")

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual([movie.movie_id for movie in movies], ["1", "2", "3"])

    def test_invalid_limits_raise_value_error_before_cache_lookup(self) -> None:
        repository, provider, cache = self.make_dependencies()
        service = self.make_service(repository, provider, cache)

        with self.assertRaises(ValueError):
            service.get_recommendation_payload(user_id="1", limit=0)

        self.assertEqual(cache.get_calls, 0)
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
