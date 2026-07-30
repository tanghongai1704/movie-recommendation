import copy
import os
import sys
import types
import unittest
from typing import Any

from fastapi.testclient import TestClient


class FakeDynamoDBTable:
    """Small in-memory DynamoDB test double for API composition tests."""

    KEY_FIELDS = {
        "Movies": ("movie_id",),
        "PopularMovies": ("list_id",),
        "Users": ("user_id",),
        "UserInteractions": ("user_id", "interaction_key"),
        "RecommendationCache": ("user_id", "scenario"),
    }

    def __init__(self, name: str) -> None:
        self.name = name
        self.items: dict[tuple[Any, ...], dict[str, Any]] = {}

    def clear(self) -> None:
        self.items.clear()

    def put_item(self, *, Item: dict[str, Any], **_: Any) -> dict[str, Any]:
        self.items[self._key(Item)] = dict(Item)
        return {}

    def get_item(self, *, Key: dict[str, Any]) -> dict[str, Any]:
        item = self.items.get(self._key(Key))
        return {"Item": dict(item)} if item is not None else {}

    def scan(self, **_: Any) -> dict[str, Any]:
        return {"Items": [dict(item) for item in self.items.values()]}

    def query(self, **options: Any) -> dict[str, Any]:
        partition_key = options["ExpressionAttributeNames"]["#pk"]
        partition_value = options["ExpressionAttributeValues"][":pk"]
        return {
            "Items": [
                dict(item)
                for item in self.items.values()
                if item.get(partition_key) == partition_value
            ]
        }

    def _key(self, item: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(item[field] for field in self.KEY_FIELDS[self.name])


TABLES = {
    name: FakeDynamoDBTable(name)
    for name in FakeDynamoDBTable.KEY_FIELDS
}


class FakeDynamoDBResource:
    def Table(self, name: str) -> FakeDynamoDBTable:
        return TABLES[name]

    def batch_get_item(
        self,
        *,
        RequestItems: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        responses: dict[str, list[dict[str, Any]]] = {}
        for table_name, options in RequestItems.items():
            table = TABLES[table_name]
            responses[table_name] = [
                dict(item)
                for key in options.get("Keys", [])
                if (item := table.items.get(table._key(key))) is not None
            ]
        return {"Responses": responses, "UnprocessedKeys": {}}


for legacy_name in (
    "AWS_DYNAMODB_TABLE_MOVIES",
    "AWS_DYNAMODB_TABLE_POPULAR",
    "AWS_DYNAMODB_TABLE_USERS",
    "AWS_DYNAMODB_TABLE_INTERACTIONS",
    "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE",
):
    os.environ.pop(legacy_name, None)


os.environ.update(
    {
        "JWT_SECRET": "http-flow-test-secret-with-at-least-32-bytes",
        "AWS_REGION": "ap-southeast-1",
        "AWS_DYNAMODB_MOVIES_TABLE": "Movies",
        "AWS_DYNAMODB_POPULAR_TABLE": "PopularMovies",
        "AWS_DYNAMODB_USERS_TABLE": "Users",
        "AWS_DYNAMODB_INTERACTIONS_TABLE": "UserInteractions",
        "AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE": "RecommendationCache",
        "AWS_S3_BUCKET": "test-movie-recommendation-bucket",
        "AWS_VALIDATE_CREDENTIALS": "False",
        "AWS_VALIDATE_RESOURCES": "False",
        "AWS_DYNAMODB_POPULAR_LIST_ID": "top_rated_all",
        "AWS_S3_DATASET_PREFIX": "app/test/data/",
        "AWS_S3_RAW_PREFIX": "app/test/data/raw/",
        "AWS_S3_PROCESSED_PREFIX": "app/test/data/processed/",
        "AWS_S3_SERVING_PREFIX": "app/test/data/serving/",
        "AWS_S3_TRAINING_PREFIX": "app/test/data/splits/",
        "AWS_S3_MODEL_PREFIX": "app/test/artifacts/",
        "AWS_S3_OUTPUT_PREFIX": "app/test/reports/",
        "AWS_S3_INTERACTION_EXPORT_PREFIX": "app/test/events/",
        "PASSWORD_HASH_ITERATIONS": "10000",
        "ALLOW_LEGACY_DEV_LOGIN": "True",
    }
)
class FakeBoto3Session:
    def __init__(self, **_options: Any) -> None:
        pass

    def resource(self, *_args: Any, **_kwargs: Any) -> FakeDynamoDBResource:
        return FakeDynamoDBResource()

    def client(self, *_args: Any, **_kwargs: Any) -> Any:
        return types.SimpleNamespace()


sys.modules["boto3"] = types.SimpleNamespace(Session=FakeBoto3Session)

from app.main import app


class AuthenticationHTTPFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        for table in TABLES.values():
            table.clear()
        TABLES["PopularMovies"].put_item(
            Item={
                "list_id": "top_rated_all",
                "ranking_type": "ALL",
                "genre": "ALL",
                "movie_ids": [],
                "scores": [],
                "generated_at": "2026-07-28T00:00:00Z",
            }
        )
        self.client = TestClient(app)

    def test_first_login_must_complete_onboarding_for_recommendations(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewer@example.com",
                "username": "viewer",
                "password": "password123",
            },
        )

        self.assertEqual(register.status_code, 201)
        session = register.json()
        self.assertEqual(session["token_type"], "bearer")
        self.assertEqual(session["user"]["user_state"], "first_login")
        self.assertNotIn("password_hash", session["user"])
        headers = {"Authorization": f"Bearer {session['access_token']}"}

        profile = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(profile.status_code, 200)

        blocked = self.client.get(
            f"/api/v1/recommend/{session['user']['user_id']}",
            headers=headers,
        )
        self.assertEqual(blocked.status_code, 403)

        too_many_genres = self.client.put(
            "/api/v1/users/me/onboarding",
            headers=headers,
            json={
                "onboarding_genres": [
                    "Drama",
                    "Comedy",
                    "Science Fiction",
                    "Thriller",
                ]
            },
        )
        self.assertEqual(too_many_genres.status_code, 422)

        onboarding = self.client.put(
            "/api/v1/users/me/onboarding",
            headers=headers,
            json={"onboarding_genres": ["Drama", "Science Fiction"]},
        )
        self.assertEqual(onboarding.status_code, 200)
        self.assertEqual(onboarding.json()["user_state"], "returning_user")
        TABLES["Movies"].put_item(
            Item={
                "movie_id": "265330",
                "title": "Cached movie",
                "release_year": 2024,
                "genres": ["Drama"],
                "overview": "Loaded from DynamoDB.",
                "poster_path": "/poster.jpg",
                "vote_average": 8.0,
                "vote_count": 100,
                "popularity": 20.0,
                "runtime": 100,
                "original_language": "en",
                "companies": ["Studio"],
                "countries": ["Vietnam"],
                "actors": ["Actor"],
                "directors": ["Director"],
            }
        )
        TABLES["RecommendationCache"].put_item(
            Item={
                "user_id": session["user"]["user_id"],
                "scenario": "onboarding_user",
                "items": [
                    {
                        "movie_id": "265330",
                        "score": 0.9,
                        "reason_code": "cache_hit",
                    }
                ],
                "model_version": "deployed-cache-v1",
                "generated_at": "2026-07-28T00:00:00Z",
                "expire_at": 4_102_444_800,
            }
        )

        recommendations = self.client.get(
            f"/api/v1/recommend/{session['user']['user_id']}",
            headers=headers,
        )
        self.assertEqual(recommendations.status_code, 200)

    def test_guest_and_invalid_token_access_policy(self) -> None:
        self.assertEqual(self.client.get("/api/v1/movies").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(
            self.client.post("/api/v1/auth/logout").status_code,
            401,
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/movies",
                headers={"Authorization": "Bearer invalid"},
            ).status_code,
            401,
        )

    def test_movie_detail_reads_every_field_from_movies_table(self) -> None:
        movie = {
            "movie_id": "265330",
            "title": "TMDB-backed movie",
            "release_year": 2024,
            "genres": ["Drama", "Thriller"],
            "overview": "Canonical metadata loaded from the Movies table.",
            "poster_path": "/3LdEtd3IMJtw4zitgWZpIc60UFX.jpg",
            "vote_average": 7.8,
            "vote_count": 1234,
            "popularity": 42.5,
            "runtime": 100,
            "original_language": "en",
            "companies": ["Example Pictures"],
            "countries": ["United States"],
            "actors": ["Actor One", "Actor Two"],
            "directors": ["Director One"],
        }
        TABLES["Movies"].put_item(Item=movie)

        response = self.client.get("/api/v1/movie/265330")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), movie)

    def test_interaction_retry_reuses_event_id_and_storage_key(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "interaction@example.com",
                "username": "interaction-user",
                "password": "password123",
            },
        )
        self.assertEqual(register.status_code, 201)
        token = register.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "interaction-request-00000001",
        }
        payload = {
            "interaction_type": "reaction",
            "interaction_action": "set",
            "interaction_value": 1,
            "movie_id": "265330",
            "timestamp": "2026-07-28T12:00:00Z",
            "session_id": "session-1",
        }

        first = self.client.post(
            "/api/v1/users/me/interactions",
            headers=headers,
            json=payload,
        )
        retry = self.client.post(
            "/api/v1/users/me/interactions",
            headers=headers,
            json=payload,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(first.json(), retry.json())
        interaction = first.json()
        self.assertEqual(interaction["interaction_type"], "reaction")
        self.assertEqual(interaction["interaction_action"], "set")
        self.assertEqual(interaction["interaction_value"], 1)
        self.assertIn(interaction["event_id"], interaction["interaction_key"])
        self.assertEqual(
            len(TABLES["UserInteractions"].items),
            1,
        )

    def test_interaction_requires_idempotency_key(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "missing-key@example.com",
                "username": "missing-key-user",
                "password": "password123",
            },
        )
        token = register.json()["access_token"]

        response = self.client.post(
            "/api/v1/users/me/interactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "interaction_type": "share",
                "interaction_action": "record",
                "interaction_value": 1,
                "movie_id": "265330",
                "timestamp": "2026-07-28T12:00:00Z",
                "session_id": "session-1",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_current_user_rating_returns_latest_rating_or_null(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "rating@example.com",
                "username": "rating-user",
                "password": "password123",
            },
        )
        token = register.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        unrated = self.client.get(
            "/api/v1/users/me/ratings/265330",
            headers=auth_headers,
        )
        self.assertEqual(
            unrated.json(),
            {"movie_id": "265330", "rating": None},
        )

        for index, (timestamp, rating) in enumerate(
            [
                ("2026-07-28T12:00:00Z", 2.0),
                ("2026-07-28T13:00:00Z", 4.0),
            ],
            start=1,
        ):
            response = self.client.post(
                "/api/v1/users/me/interactions",
                headers={
                    **auth_headers,
                    "Idempotency-Key": f"rating-request-{index:08d}",
                },
                json={
                    "interaction_type": "rating",
                    "interaction_action": "set",
                    "interaction_value": rating,
                    "movie_id": "265330",
                    "timestamp": timestamp,
                    "session_id": "session-1",
                },
            )
            self.assertEqual(response.status_code, 201)

        rated = self.client.get(
            "/api/v1/users/me/ratings/265330",
            headers=auth_headers,
        )

        self.assertEqual(
            rated.json(),
            {"movie_id": "265330", "rating": 4.0},
        )

        cleared = self.client.post(
            "/api/v1/users/me/interactions",
            headers={
                **auth_headers,
                "Idempotency-Key": "rating-clear-request-00000001",
            },
            json={
                "interaction_type": "rating",
                "interaction_action": "clear",
                "interaction_value": 0,
                "movie_id": "265330",
                "timestamp": "2026-07-28T14:00:00Z",
                "session_id": "session-1",
            },
        )
        self.assertEqual(cleared.status_code, 201)
        self.assertIsNone(
            self.client.get(
                "/api/v1/users/me/ratings/265330",
                headers=auth_headers,
            ).json()["rating"]
        )

    def test_current_user_rating_reads_legacy_interaction_records(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "legacy-rating@example.com",
                "username": "legacy-rating-user",
                "password": "password123",
            },
        )
        session = register.json()
        user_id = session["user"]["user_id"]
        auth_headers = {
            "Authorization": f"Bearer {session['access_token']}"
        }
        TABLES["UserInteractions"].put_item(
            Item={
                "user_id": user_id,
                "interaction_key": "2026-07-28T12:00:00Z#265330",
                "event_id": "legacy-event-id",
                "event_type": "rating",
                "movie_id": 265330,
                "rating": 3.5,
                "created_at": "2026-07-28T12:00:00Z",
                "metadata": {"source": "seed"},
                "schema_version": 1,
                "username": "legacy-rating-user",
            }
        )

        response = self.client.get(
            "/api/v1/users/me/ratings/265330",
            headers=auth_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"movie_id": "265330", "rating": 3.5},
        )

    def test_current_user_reaction_tracks_set_and_clear(self) -> None:
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "reaction@example.com",
                "username": "reaction-user",
                "password": "password123",
            },
        )
        token = register.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        endpoint = "/api/v1/users/me/reactions/265330"

        self.assertIsNone(
            self.client.get(endpoint, headers=auth_headers).json()["reaction"]
        )

        for index, (timestamp, action, value, expected) in enumerate(
            [
                ("2026-07-28T12:00:00Z", "set", 1, "like"),
                ("2026-07-28T13:00:00Z", "set", -1, "dislike"),
                ("2026-07-28T14:00:00Z", "clear", 0, None),
            ],
            start=1,
        ):
            stored = self.client.post(
                "/api/v1/users/me/interactions",
                headers={
                    **auth_headers,
                    "Idempotency-Key": f"reaction-change-{index:08d}",
                },
                json={
                    "interaction_type": "reaction",
                    "interaction_action": action,
                    "interaction_value": value,
                    "movie_id": "265330",
                    "timestamp": timestamp,
                    "session_id": "session-1",
                },
            )
            self.assertEqual(stored.status_code, 201)
            self.assertEqual(
                self.client.get(
                    endpoint,
                    headers=auth_headers,
                ).json()["reaction"],
                expected,
            )

    def test_legacy_seed_login_does_not_rewrite_users_item(self) -> None:
        TABLES["Users"].put_item(
            Item={
                "user_id": "1",
                "recent_movie_ids": ["10", "20"],
                "schema_version": 2,
                "onboarding_genres": None,
                "user_settings": {
                    "email": "1@email.com",
                    "username": "1#username",
                    "password_hash": "1#pass",
                    "created_at": "2020-01-01T00:00:00Z",
                },
            }
        )
        before_login = copy.deepcopy(TABLES["Users"].items)

        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "1#username", "password": "1#pass"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["user_id"], "1")
        self.assertEqual(response.json()["user"]["user_state"], "first_login")
        self.assertEqual(TABLES["Users"].items, before_login)


if __name__ == "__main__":
    unittest.main()
