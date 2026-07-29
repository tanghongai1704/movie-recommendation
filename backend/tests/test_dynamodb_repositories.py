import unittest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.models.movie import Movie
from app.models.popular_movie import PopularMovie
from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.models.user import User, UserSettings
from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    UserInteraction,
)
from app.repositories.movies_repository import MoviesRepository
from app.repositories.popular_movies_repository import PopularMoviesRepository
from app.repositories.recommendation_cache_repository import (
    RecommendationCacheRepository,
)
from app.repositories.user_interactions_repository import (
    UserInteractionsRepository,
)
from app.repositories.users_repository import UsersRepository


class FakeConditionalError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": message,
            }
        }


class FakeDynamoDBTable:
    """Minimal DynamoDB table double used to verify repository mapping."""

    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    @staticmethod
    def _key_fields(item: dict[str, Any]) -> tuple[str, ...]:
        if "interaction_key" in item:
            return ("user_id", "interaction_key")
        if "scenario" in item:
            return ("user_id", "scenario")
        if "list_id" in item:
            return ("list_id",)
        if "movie_id" in item:
            return ("movie_id",)
        return ("user_id",)

    @staticmethod
    def _matches(item: dict[str, Any], key: dict[str, Any]) -> bool:
        return all(item.get(name) == value for name, value in key.items())

    def put_item(self, *, Item: dict[str, Any], **options: Any) -> dict[str, Any]:
        key = {name: Item[name] for name in self._key_fields(Item)}
        existing = next(
            (item for item in self.items if self._matches(item, key)),
            None,
        )
        condition = options.get("ConditionExpression", "")
        if "attribute_not_exists" in condition and existing is not None:
            raise FakeConditionalError("Item already exists")
        if "attribute_exists" in condition and existing is None:
            raise FakeConditionalError("Item does not exist")
        self.items = [item for item in self.items if not self._matches(item, key)]
        self.items.append(Item)
        return {}

    def get_item(self, *, Key: dict[str, Any]) -> dict[str, Any]:
        item = next(
            (item for item in self.items if self._matches(item, Key)),
            None,
        )
        return {"Item": item} if item is not None else {}

    def delete_item(
        self,
        *,
        Key: dict[str, Any],
        ReturnValues: str,
    ) -> dict[str, Any]:
        del ReturnValues
        existing = next(
            (item for item in self.items if self._matches(item, Key)),
            None,
        )
        self.items = [item for item in self.items if not self._matches(item, Key)]
        return {"Attributes": existing} if existing is not None else {}

    def scan(self, **options: Any) -> dict[str, Any]:
        limit = options.get("Limit")
        items = self.items if limit is None else self.items[:limit]
        return {"Items": list(items)}

    def query(self, **options: Any) -> dict[str, Any]:
        partition_key = options["ExpressionAttributeNames"]["#pk"]
        partition_value = options["ExpressionAttributeValues"][":pk"]
        return {
            "Items": [
                item
                for item in self.items
                if item.get(partition_key) == partition_value
            ]
        }


class FakeBatchReader:
    def __init__(self, table_name: str, table: FakeDynamoDBTable) -> None:
        self.table_name = table_name
        self.table = table
        self.calls = 0

    def batch_get_item(
        self,
        *,
        RequestItems: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        self.calls += 1
        keys = RequestItems[self.table_name]["Keys"]
        items = [
            item
            for key in keys
            if (
                item := next(
                    (
                        candidate
                        for candidate in self.table.items
                        if self.table._matches(candidate, key)
                    ),
                    None,
                )
            )
            is not None
        ]
        return {
            "Responses": {self.table_name: list(reversed(items))},
            "UnprocessedKeys": {},
        }


class DynamoDBRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timestamp = datetime(2026, 7, 28, tzinfo=timezone.utc)

    def make_movie(
        self,
        *,
        movie_id: str = "movie-1",
        title: str = "Example",
    ) -> Movie:
        return Movie(
            movie_id=movie_id,
            title=title,
            release_year=2026,
            genres=["Drama"],
            overview="Overview",
            poster_path="/poster.jpg",
            vote_average=8.0,
            vote_count=100,
            popularity=25.0,
            runtime=110,
            original_language="en",
            companies=["Studio"],
            countries=["Vietnam"],
            actors=["Actor"],
            directors=["Director"],
        )

    def test_movies_repository_crud(self) -> None:
        repository = MoviesRepository(
            table_name="movies-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        movie = self.make_movie()

        self.assertEqual(repository.create(movie), movie)
        self.assertEqual(repository.get("movie-1"), movie)
        self.assertEqual(repository.list_all(), [movie])

        updated = self.make_movie(title="Updated")
        self.assertEqual(repository.update(updated), updated)
        self.assertEqual(repository.get("movie-1"), updated)
        self.assertTrue(repository.delete("movie-1"))
        self.assertIsNone(repository.get("movie-1"))

    def test_movies_repository_applies_read_limit(self) -> None:
        repository = MoviesRepository(
            table_name="movies-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        first = self.make_movie(movie_id="movie-1")
        second = self.make_movie(movie_id="movie-2")
        repository.create(first)
        repository.create(second)

        self.assertEqual(repository.list_all(limit=1), [first])

    def test_movies_repository_batch_get_preserves_requested_order(self) -> None:
        table = FakeDynamoDBTable()
        batch_reader = FakeBatchReader("movies-test", table)
        repository = MoviesRepository(
            table_name="movies-test",
            region_name="test-region",
            table=table,
            batch_reader=batch_reader,
        )
        first = self.make_movie(movie_id="movie-1")
        second = self.make_movie(movie_id="movie-2")
        repository.create(first)
        repository.create(second)

        movies = repository.get_many(["movie-2", "movie-1", "missing"])

        self.assertEqual(movies, [second, first])
        self.assertEqual(batch_reader.calls, 1)

    def test_popular_movies_repository_crud(self) -> None:
        repository = PopularMoviesRepository(
            table_name="popular-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        popular = PopularMovie(
            list_id="global",
            ranking_type="global",
            genre=None,
            movie_ids=["movie-1"],
            scores=[0.9],
            generated_at=self.timestamp,
        )

        self.assertEqual(repository.create(popular), popular)
        self.assertEqual(repository.get("global"), popular)
        self.assertEqual(repository.list_all(), [popular])
        self.assertEqual(repository.update(popular), popular)
        self.assertTrue(repository.delete("global"))

    def test_popular_movies_normalizes_deployed_numeric_movie_ids(self) -> None:
        table = FakeDynamoDBTable()
        table.items.append(
            {
                "list_id": "top_rated_all",
                "ranking_type": "ALL",
                "genre": "ALL",
                "movie_ids": [Decimal("278"), Decimal("238")],
                "scores": [Decimal("9.0"), Decimal("8.9")],
                "generated_at": self.timestamp.isoformat(),
            }
        )
        repository = PopularMoviesRepository(
            table_name="popular-test",
            region_name="test-region",
            table=table,
        )

        ranking = repository.get("top_rated_all")

        self.assertIsNotNone(ranking)
        self.assertEqual(ranking.movie_ids, ["278", "238"])

    def test_users_repository_crud(self) -> None:
        repository = UsersRepository(
            table_name="users-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        user = User(
            user_id="user-1",
            recent_movie_ids=["movie-1"],
            schema_version=2,
            onboarding_genres=["Drama"],
            user_settings=UserSettings(
                email="user@example.com",
                username="example",
                password_hash="hash",
                created_at=self.timestamp,
            ),
        )

        self.assertEqual(repository.create(user), user)
        self.assertEqual(repository.get("user-1"), user)
        self.assertEqual(repository.list_all(), [user])
        self.assertEqual(repository.update(user), user)
        self.assertTrue(repository.delete("user-1"))

    def test_user_interactions_repository_crud(self) -> None:
        repository = UserInteractionsRepository(
            table_name="interactions-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        interaction = UserInteraction(
            user_id="user-1",
            interaction_key=(
                "2026-07-28T00:00:00.000Z#movie-1"
                "#00000000-0000-4000-8000-000000000001"
            ),
            event_id=UUID("00000000-0000-4000-8000-000000000001"),
            movie_id="movie-1",
            interaction_type=InteractionType.WATCH,
            interaction_action=InteractionAction.RECORD,
            interaction_value=0.6,
            timestamp=self.timestamp,
            session_id="session-1",
        )

        self.assertEqual(repository.create(interaction), interaction)
        self.assertEqual(
            repository.get("user-1", interaction.interaction_key),
            interaction,
        )
        self.assertEqual(repository.create(interaction), interaction)
        listed = repository.list_by_user("user-1")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].user_id, interaction.user_id)
        self.assertEqual(listed[0].interaction_key, interaction.interaction_key)
        self.assertEqual(listed[0].movie_id, interaction.movie_id)
        self.assertEqual(
            listed[0].interaction_type,
            interaction.interaction_type,
        )
        self.assertEqual(
            listed[0].interaction_action,
            interaction.interaction_action,
        )
        self.assertEqual(
            listed[0].interaction_value,
            interaction.interaction_value,
        )
        self.assertEqual(listed[0].timestamp, interaction.timestamp)
        self.assertEqual(repository.update(interaction), interaction)
        self.assertTrue(
            repository.delete("user-1", interaction.interaction_key)
        )

    def test_user_interactions_repository_normalizes_legacy_reads(self) -> None:
        table = FakeDynamoDBTable()
        repository = UserInteractionsRepository(
            table_name="interactions-test",
            region_name="test-region",
            table=table,
        )
        table.items.extend(
            [
                {
                    "user_id": "user-1",
                    "interaction_key": (
                        "2026-07-28T12:00:00.000Z#movie-1"
                        "#legacy-generated-event"
                    ),
                    "movie_id": "movie-1",
                    "interaction_type": "rating",
                    "interaction_action": "set",
                    "interaction_value": Decimal("4.5"),
                    "timestamp": "2026-07-28T12:00:00Z",
                    "session_id": None,
                },
                {
                    "user_id": "user-1",
                    "interaction_key": "2026-07-28T13:00:00Z#42",
                    "event_id": "legacy-event-id",
                    "event_type": "rating",
                    "movie_id": 42,
                    "rating": Decimal("3.5"),
                    "created_at": "2026-07-28T13:00:00Z",
                    "metadata": {"source": "seed"},
                    "schema_version": Decimal("1"),
                    "username": "legacy-user",
                },
                {
                    "user_id": "user-1",
                    "interaction_key": "2026-07-28T14:00:00Z#movie-2",
                    "movie_id": "movie-2",
                    "interaction_type": "reaction",
                    "interaction_value": Decimal("-1"),
                    "timestamp": "2026-07-28T14:00:00Z",
                    "session_id": "legacy-session",
                },
                {
                    "user_id": "user-1",
                    "interaction_key": "2026-07-28T15:00:00Z#movie-3",
                    "movie_id": "movie-3",
                    "interaction_type": "rating",
                    "interaction_action": "set",
                    "interaction_value": Decimal("0"),
                    "timestamp": "2026-07-28T15:00:00Z",
                    "session_id": None,
                },
            ]
        )

        records = repository.list_by_user("user-1")

        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].interaction_value, 4.5)
        self.assertEqual(records[1].movie_id, "42")
        self.assertEqual(
            records[1].interaction_type,
            InteractionType.RATING,
        )
        self.assertEqual(
            records[1].interaction_action,
            InteractionAction.SET,
        )
        self.assertEqual(records[1].interaction_value, 3.5)
        self.assertEqual(
            records[2].interaction_action,
            InteractionAction.SET,
        )
        self.assertEqual(records[2].interaction_value, -1)
        self.assertEqual(
            records[3].interaction_action,
            InteractionAction.CLEAR,
        )

    def test_recommendation_cache_repository_crud_and_upsert(self) -> None:
        repository = RecommendationCacheRepository(
            table_name="cache-test",
            region_name="test-region",
            table=FakeDynamoDBTable(),
        )
        cache_entry = RecommendationCache(
            user_id="user-1",
            scenario="home",
            items=[
                RecommendationCacheItem(
                    movie_id="movie-1",
                    score=0.95,
                    reason_code="genre_match",
                )
            ],
            model_version="cache-v1",
            generated_at=self.timestamp,
            expire_at=1_800_000_000,
        )

        self.assertEqual(repository.create(cache_entry), cache_entry)
        self.assertEqual(repository.get("user-1", "home"), cache_entry)
        self.assertEqual(repository.update(cache_entry), cache_entry)
        self.assertEqual(repository.upsert(cache_entry), cache_entry)
        self.assertTrue(repository.delete("user-1", "home"))

    def test_recommendation_cache_ignores_legacy_mock_record(self) -> None:
        table = FakeDynamoDBTable()
        table.items.append(
            {
                "user_id": "user-1",
                "scenario": "default",
                "provider": "MockRecommendationProvider",
                "movie_ids": [Decimal("1")],
                "movies": [{"id": Decimal("1"), "score": Decimal("8.9")}],
                "cached_at": self.timestamp.isoformat(),
                "expires_at": Decimal("1800000000"),
            }
        )
        repository = RecommendationCacheRepository(
            table_name="cache-test",
            region_name="test-region",
            table=table,
        )

        self.assertIsNone(repository.get("user-1", "default"))

    def test_table_configuration_is_required(self) -> None:
        with self.assertRaises(ValueError):
            MoviesRepository(
                table_name="",
                region_name="test-region",
                table=FakeDynamoDBTable(),
            )


if __name__ == "__main__":
    unittest.main()
