import unittest
from typing import Optional

from app.core.security import PasswordHasher
from app.models.user import User
from app.services.auth_service import (
    AccountConflictError,
    AuthService,
    InvalidCredentialsError,
)


class InMemoryUserStore:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def create(self, user: User) -> User:
        self.users[user.user_id] = user
        return user

    def get(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def list_all(self) -> list[User]:
        return list(self.users.values())

    def update(self, user: User) -> User:
        self.users[user.user_id] = user
        return user


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.users = InMemoryUserStore()
        self.hasher = PasswordHasher(iterations=10_000)
        self.service = AuthService(
            users=self.users,
            password_hasher=self.hasher,
        )

    def register_user(self) -> User:
        return self.service.register(
            email="viewer@example.com",
            username="viewer",
            password="password123",
        )

    def test_register_hashes_password_and_creates_first_login_user(self) -> None:
        user = self.register_user()

        self.assertNotEqual(user.password_hash, "password123")
        self.assertTrue(
            self.hasher.verify_password("password123", user.password_hash)
        )
        self.assertFalse(user.onboarding_completed)
        self.assertEqual(user.onboarding_genres, [])

    def test_register_rejects_duplicate_email_or_username(self) -> None:
        self.register_user()

        with self.assertRaises(AccountConflictError):
            self.service.register(
                email="VIEWER@example.com",
                username="other",
                password="password123",
            )
        with self.assertRaises(AccountConflictError):
            self.service.register(
                email="other@example.com",
                username="VIEWER",
                password="password123",
            )

    def test_authenticates_with_username_or_email(self) -> None:
        registered = self.register_user()

        by_username = self.service.authenticate(
            identity="viewer",
            password="password123",
        )
        by_email = self.service.authenticate(
            identity="VIEWER@example.com",
            password="password123",
        )

        self.assertEqual(by_username.user_id, registered.user_id)
        self.assertEqual(by_email.user_id, registered.user_id)
        self.assertGreaterEqual(
            by_email.last_active_at,
            registered.last_active_at,
        )

    def test_rejects_invalid_credentials(self) -> None:
        self.register_user()

        with self.assertRaises(InvalidCredentialsError):
            self.service.authenticate(
                identity="viewer",
                password="wrong-password",
            )
        with self.assertRaises(InvalidCredentialsError):
            self.service.authenticate(
                identity="missing",
                password="password123",
            )

    def test_updates_profile_without_exposing_password_logic(self) -> None:
        user = self.register_user()

        updated = self.service.update_profile(
            user_id=user.user_id,
            email="updated@example.com",
            username="updated-viewer",
        )

        self.assertEqual(updated.email, "updated@example.com")
        self.assertEqual(updated.username, "updated-viewer")
        self.assertEqual(updated.password_hash, user.password_hash)

    def test_completes_onboarding_and_marks_returning_user(self) -> None:
        user = self.register_user()

        updated = self.service.complete_onboarding(
            user_id=user.user_id,
            onboarding_genres=["Drama", "Comedy"],
        )

        self.assertTrue(updated.onboarding_completed)
        self.assertEqual(updated.onboarding_genres, ["Drama", "Comedy"])


if __name__ == "__main__":
    unittest.main()
