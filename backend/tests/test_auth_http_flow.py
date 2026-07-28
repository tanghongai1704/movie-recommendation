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


if __name__ == "__main__":
    unittest.main()
