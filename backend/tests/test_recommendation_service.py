import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.movie import Movie
from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.models.user import User, UserSettings
from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    StoredUserInteraction,
)
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.repositories.movie_repository import MovieRepository
from app.schemas.sagemaker import SageMakerRecommendationRequest
from app.services.recommendation_provider import (
    ProviderRecommendationItem,
    ProviderRecommendationResult,
    RecommendationProvider,
    RecommendationProviderResponseError,
)
from app.services.recommendation_service import (
    MAX_MODEL_USER_ID,
    SCENARIO_ONBOARDING,
    SCENARIO_RETURNING,
    RecommendationService,
)


class TestRecommendationCache:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], RecommendationCache] = {}
        self.get_calls: list[tuple[str, str]] = []
        self.put_calls = 0
        self.read_error = False
        self.write_error = False

    def get(
        self,
        user_id: str,
        scenario: str,
    ) -> Optional[RecommendationCache]:
        self.get_calls.append((user_id, scenario))
        if self.read_error:
            raise DynamoDBRepositoryError("read failed")
        return self.items.get((user_id, scenario))

    def upsert(self, item: RecommendationCache) -> RecommendationCache:
        self.put_calls += 1
        if self.write_error:
            raise DynamoDBRepositoryError("write failed")
        self.items[(item.user_id, item.scenario)] = item
        return item


class StaticMovieRepository(MovieRepository):
    def __init__(self, missing_ids: set[str] | None = None) -> None:
        missing_ids = missing_ids or set()
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
            if str(index) not in missing_ids
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
        # BatchGetItem does not preserve request order.
        return [
            by_id[movie_id]
            for movie_id in reversed(movie_ids)
            if movie_id in by_id
        ]


class StaticUserStore:
    def __init__(self) -> None:
        self.user = User(
            user_id="42",
            recent_movie_ids=[],
            schema_version=2,
            onboarding_genres=["Drama", "Action"],
            user_settings=UserSettings(
                email="user@example.com",
                username="user",
                password_hash="hash",
                created_at=datetime.now(timezone.utc),
            ),
        )

    def get(self, user_id: str) -> Optional[User]:
        return self.user if user_id == self.user.user_id else None


class StaticInteractionStore:
    def __init__(
        self,
        interactions: list[StoredUserInteraction] | None = None,
    ) -> None:
        self.interactions = interactions or []
        self.calls = 0

    def list_by_user(self, user_id: str) -> list[StoredUserInteraction]:
        del user_id
        self.calls += 1
        return self.interactions


class CountingRecommendationProvider(RecommendationProvider):
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[SageMakerRecommendationRequest] = []

    def get_recommendations(
        self,
        request: SageMakerRecommendationRequest,
    ) -> ProviderRecommendationResult:
        self.calls += 1
        self.requests.append(request)
        items = [
            ProviderRecommendationItem(
                movie_id=str(index),
                score=score,
                reason_code="test_rank",
            )
            for index, score in zip(
                (1, 2, 3),
                (0.9, 0.8, 0.7),
                strict=True,
            )
        ]
        return ProviderRecommendationResult(
            items=items,
            model_version="1.0.0",
            scenario_applied=request.scenario_hint,
        )


def interaction(
    index: int,
    *,
    interaction_type: InteractionType = InteractionType.RATING,
    action: InteractionAction = InteractionAction.SET,
    value: float = 4.5,
    movie_id: str | None = None,
) -> StoredUserInteraction:
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=index)
    return StoredUserInteraction(
        user_id="42",
        interaction_key=f"{timestamp.isoformat()}#{index}",
        movie_id=movie_id or str(index + 1),
        interaction_type=interaction_type,
        interaction_action=action,
        interaction_value=value,
        timestamp=timestamp,
    )


class RecommendationServiceTests(unittest.TestCase):
    def make_service(
        self,
        *,
        stored_interactions: list[StoredUserInteraction] | None = None,
        cache: TestRecommendationCache | None = None,
        repository: StaticMovieRepository | None = None,
        now: float = 1_000.0,
    ) -> tuple[
        RecommendationService,
        CountingRecommendationProvider,
        TestRecommendationCache,
        StaticInteractionStore,
    ]:
        repository = repository or StaticMovieRepository()
        provider = CountingRecommendationProvider()
        cache = cache or TestRecommendationCache()
        interactions = StaticInteractionStore(stored_interactions)
        service = RecommendationService(
            provider=provider,
            cache=cache,
            movie_repository=repository,
            users=StaticUserStore(),
            interactions=interactions,
            cache_ttl_seconds=60,
            model_version="endpoint-unversioned",
            clock=lambda: now,
        )
        return service, provider, cache, interactions

    def test_onboarding_cache_miss_builds_contract_and_caches_model_version(
        self,
    ) -> None:
        service, provider, cache, _ = self.make_service()

        response = service.get_recommendation_payload(user_id="42", limit=2)

        self.assertEqual(provider.calls, 1)
        request = provider.requests[0]
        self.assertEqual(request.scenario_hint, SCENARIO_ONBOARDING)
        self.assertEqual(request.selected_genres, ["Drama", "Action"])
        self.assertEqual(request.user_id, 42)
        cached = cache.items[("42", SCENARIO_ONBOARDING)]
        self.assertEqual(cached.model_version, "1.0.0")
        self.assertEqual(cached.expire_at, 1_060)
        self.assertEqual(
            [item.movie_id for item in response.recommendations],
            ["1", "2"],
        )

    def test_returning_context_normalizes_interactions(self) -> None:
        stored = [
            interaction(1),
            interaction(2),
            interaction(3),
            interaction(
                4,
                interaction_type=InteractionType.WATCH,
                action=InteractionAction.RECORD,
                value=0.8,
            ),
            interaction(
                5,
                interaction_type=InteractionType.REACTION,
                action=InteractionAction.SET,
                value=1,
            ),
        ]
        service, provider, cache, _ = self.make_service(
            stored_interactions=stored
        )

        service.get_recommendations(user_id="42")

        request = provider.requests[0]
        self.assertEqual(request.scenario_hint, SCENARIO_RETURNING)
        self.assertEqual(request.valid_interaction_count_90d, 5)
        self.assertIn(
            "like",
            [item.event_type for item in request.recent_interactions],
        )
        self.assertIn(("42", SCENARIO_RETURNING), cache.items)

    def test_valid_returning_cache_hit_skips_interactions_and_provider(
        self,
    ) -> None:
        cache = TestRecommendationCache()
        cache.items[("42", SCENARIO_RETURNING)] = RecommendationCache(
            user_id="42",
            scenario=SCENARIO_RETURNING,
            items=[
                RecommendationCacheItem(
                    movie_id="1",
                    score=0.9,
                    reason_code="similar_users",
                )
            ],
            model_version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            expire_at=2_000,
        )
        service, provider, _, interactions = self.make_service(cache=cache)

        movies = service.get_recommendations(user_id="42")

        self.assertEqual(provider.calls, 0)
        self.assertEqual(interactions.calls, 0)
        self.assertEqual([item.movie_id for item in movies], ["1"])

    def test_expired_cache_invokes_provider(self) -> None:
        cache = TestRecommendationCache()
        cache.items[("42", SCENARIO_RETURNING)] = RecommendationCache(
            user_id="42",
            scenario=SCENARIO_RETURNING,
            items=[],
            model_version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            expire_at=999,
        )
        service, provider, _, _ = self.make_service(cache=cache)

        service.get_recommendations(user_id="42")

        self.assertEqual(provider.calls, 1)

    def test_cache_read_and_write_errors_do_not_hide_model_result(self) -> None:
        cache = TestRecommendationCache()
        cache.read_error = True
        cache.write_error = True
        service, provider, _, _ = self.make_service(cache=cache)

        movies = service.get_recommendations(user_id="42")

        self.assertEqual(provider.calls, 1)
        self.assertEqual([item.movie_id for item in movies], ["1", "2", "3"])

    def test_missing_movie_is_skipped_without_losing_provider_order(self) -> None:
        repository = StaticMovieRepository(missing_ids={"2"})
        service, _, _, _ = self.make_service(repository=repository)

        movies = service.get_recommendations(user_id="42")

        self.assertEqual([item.movie_id for item in movies], ["1", "3"])

    def test_no_resolvable_movie_ids_is_a_provider_response_error(self) -> None:
        repository = StaticMovieRepository(missing_ids={"1", "2", "3"})
        service, _, _, _ = self.make_service(repository=repository)

        with self.assertRaises(RecommendationProviderResponseError):
            service.get_recommendations(user_id="42")

    def test_latest_clear_removes_previous_rating_from_model_context(self) -> None:
        stored = [
            interaction(
                1,
                action=InteractionAction.CLEAR,
                value=0,
                movie_id="1",
            ),
            interaction(2, action=InteractionAction.SET, value=5, movie_id="1"),
        ]
        service, provider, _, _ = self.make_service(
            stored_interactions=stored
        )

        service.get_recommendations(user_id="42")

        self.assertEqual(provider.requests[0].recent_interactions, [])

    def test_current_dislike_is_sent_as_an_explicit_exclusion(self) -> None:
        stored = [
            interaction(
                1,
                interaction_type=InteractionType.REACTION,
                action=InteractionAction.SET,
                value=-1,
                movie_id="550",
            )
        ]
        service, provider, _, _ = self.make_service(
            stored_interactions=stored
        )

        service.get_recommendations(user_id="42")

        request = provider.requests[0]
        self.assertEqual(request.exclude_movie_ids, [550])
        self.assertEqual(
            request.recent_interactions[0].event_type,
            "dislike",
        )

    def test_uuid_user_mapping_is_stable_and_int64_safe(self) -> None:
        user_id = "3a1985e5-3e2a-4203-9017-7423aabdd330"

        first = RecommendationService._model_user_id(user_id)
        second = RecommendationService._model_user_id(user_id)

        self.assertEqual(first, second)
        self.assertGreater(first, 0)
        self.assertLessEqual(first, MAX_MODEL_USER_ID)

    def test_invalid_limits_fail_before_repository_calls(self) -> None:
        service, provider, cache, interactions = self.make_service()

        with self.assertRaises(ValueError):
            service.get_recommendation_payload(user_id="42", limit=0)

        self.assertEqual(provider.calls, 0)
        self.assertEqual(cache.get_calls, [])
        self.assertEqual(interactions.calls, 0)


if __name__ == "__main__":
    unittest.main()
