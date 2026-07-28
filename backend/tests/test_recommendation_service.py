import unittest
from typing import Optional

from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.recommendation_provider import RecommendationProvider
from app.services.recommendation_service import RecommendationService


class InMemoryRecommendationCache:
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


class CountingRecommendationProvider(RecommendationProvider):
    def __init__(self, repository: InMemoryMovieRepository) -> None:
        self.calls = 0
        self._provider = MockRecommendationProvider(repository=repository)

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        self.calls += 1
        return self._provider.get_recommendations(user_id=user_id)


class RecommendationServiceTests(unittest.TestCase):
    def make_dependencies(
        self,
    ) -> tuple[
        InMemoryMovieRepository,
        CountingRecommendationProvider,
        InMemoryRecommendationCache,
    ]:
        repository = InMemoryMovieRepository()
        return (
            repository,
            CountingRecommendationProvider(repository),
            InMemoryRecommendationCache(),
        )

    def make_service(
        self,
        repository: InMemoryMovieRepository,
        provider: CountingRecommendationProvider,
        cache: InMemoryRecommendationCache,
        now: float = 1_000.0,
    ) -> RecommendationService:
        return RecommendationService(
            provider=provider,
            cache=cache,
            movie_repository=repository,
            cache_ttl_seconds=60,
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
        self.assertEqual(cached.model_version, "mock-v1")
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
        self.assertEqual(second.recommendations[0].title, "Midnight Horizon")
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
