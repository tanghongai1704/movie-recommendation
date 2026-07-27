import unittest
from typing import Any, Optional

from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.recommendation_provider import RecommendationProvider
from app.services.recommendation_service import RecommendationService


class InMemoryRecommendationCache:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, Any]] = {}
        self.get_calls = 0
        self.put_calls = 0

    def get_item(self, user_id: Any, scenario: str) -> Optional[dict[str, Any]]:
        self.get_calls += 1
        return self.items.get((str(user_id), scenario))

    def put_item(self, item: dict[str, Any]) -> dict[str, Any]:
        self.put_calls += 1
        self.items[(item["user_id"], item["scenario"])] = item
        return item


class CountingRecommendationProvider(RecommendationProvider):
    def __init__(self) -> None:
        self.calls = 0
        self._provider = MockRecommendationProvider(
            repository=InMemoryMovieRepository()
        )

    def get_recommendations(
        self,
        user_id: Optional[int] = None,
    ) -> list[MovieResponse]:
        self.calls += 1
        return self._provider.get_recommendations(user_id=user_id)


class RecommendationServiceTests(unittest.TestCase):
    def make_service(
        self,
        provider: CountingRecommendationProvider,
        cache: InMemoryRecommendationCache,
        now: float = 1_000.0,
    ) -> RecommendationService:
        return RecommendationService(
            provider=provider,
            cache=cache,
            cache_ttl_seconds=60,
            clock=lambda: now,
        )

    def test_cache_miss_calls_provider_and_saves_ordered_movie_ids(self) -> None:
        provider = CountingRecommendationProvider()
        cache = InMemoryRecommendationCache()
        service = self.make_service(provider, cache)

        response = service.get_recommendation_payload(user_id=42, limit=2)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.get_calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual(
            cache.items[("42", "default")]["movie_ids"],
            [1, 2, 3],
        )
        self.assertEqual(response.user_id, 42)
        self.assertEqual(
            [item.movie_id for item in response.recommendations],
            [1, 2],
        )

    def test_valid_cache_hit_does_not_call_provider(self) -> None:
        provider = CountingRecommendationProvider()
        cache = InMemoryRecommendationCache()
        service = self.make_service(provider, cache)
        first = service.get_recommendation_payload(user_id=42)

        second = service.get_recommendation_payload(user_id=42)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual(second, first)
        self.assertEqual(second.recommendations[0].score, 8.9)

    def test_expired_cache_calls_provider_and_replaces_entry(self) -> None:
        provider = CountingRecommendationProvider()
        cache = InMemoryRecommendationCache()
        service = self.make_service(provider, cache, now=1_000.0)
        service.get_recommendations(user_id=7)
        cache.items[("7", "default")]["expires_at"] = 999
        provider.calls = 0
        cache.put_calls = 0

        service.get_recommendations(user_id=7)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual(cache.items[("7", "default")]["expires_at"], 1_060)

    def test_invalid_cache_calls_provider_and_replaces_entry(self) -> None:
        provider = CountingRecommendationProvider()
        cache = InMemoryRecommendationCache()
        service = self.make_service(provider, cache)
        service.get_recommendations(user_id=9)
        cache.items[("9", "default")]["movie_ids"] = [999]
        provider.calls = 0
        cache.put_calls = 0

        movies = service.get_recommendations(user_id=9)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(cache.put_calls, 1)
        self.assertEqual([movie.id for movie in movies], [1, 2, 3])

    def test_invalid_limits_raise_value_error_before_cache_lookup(self) -> None:
        provider = CountingRecommendationProvider()
        cache = InMemoryRecommendationCache()
        service = self.make_service(provider, cache)

        with self.assertRaises(ValueError):
            service.get_recommendation_payload(user_id=1, limit=0)

        self.assertEqual(cache.get_calls, 0)
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
