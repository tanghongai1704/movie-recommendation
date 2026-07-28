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

    def _key(self, item: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(item[field] for field in self.KEY_FIELDS[self.name])


TABLES = {
    name: FakeDynamoDBTable(name)
    for name in FakeDynamoDBTable.KEY_FIELDS
}

os.environ.update(
    {
        "JWT_SECRET": "http-flow-test-secret-with-at-least-32-bytes",
        "AWS_REGION": "ap-southeast-1",
        "AWS_DYNAMODB_TABLE_MOVIES": "Movies",
        "AWS_DYNAMODB_TABLE_POPULAR": "PopularMovies",
        "AWS_DYNAMODB_TABLE_USERS": "Users",
        "AWS_DYNAMODB_TABLE_INTERACTIONS": "UserInteractions",
        "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE": "RecommendationCache",
        "PASSWORD_HASH_ITERATIONS": "10000",
        "ALLOW_LEGACY_DEV_LOGIN": "True",
    }
)
sys.modules["boto3"] = types.SimpleNamespace(
    resource=lambda *_args, **_kwargs: types.SimpleNamespace(
        Table=lambda name: TABLES[name]
    )
)

from app.main import app


class AuthenticationHTTPFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        for table in TABLES.values():
            table.clear()
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
