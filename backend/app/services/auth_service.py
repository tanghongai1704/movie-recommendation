from __future__ import annotations

import hmac
from datetime import datetime, timezone
from typing import Optional, Protocol
from uuid import uuid4

from app.core.security import PasswordHashError, PasswordHasher
from app.models.user import User, UserSettings


class UserStore(Protocol):
    """Persistence operations required by authentication business logic."""

    def create(self, user: User) -> User:
        ...

    def get(self, user_id: str) -> Optional[User]:
        ...

    def list_all(self) -> list[User]:
        ...

    def update(self, user: User) -> User:
        ...


class AuthenticationError(Exception):
    """Base authentication business error."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when supplied login credentials are invalid."""


class AccountConflictError(AuthenticationError):
    """Raised when an email or username is already registered."""


class UserNotFoundError(AuthenticationError):
    """Raised when a token references a user that no longer exists."""


class AuthService:
    """Registered-user identity, credential, profile, and onboarding logic."""

    def __init__(
        self,
        *,
        users: UserStore,
        password_hasher: PasswordHasher,
        allow_legacy_dev_login: bool = False,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._allow_legacy_dev_login = allow_legacy_dev_login
        self._dummy_password_hash = password_hasher.hash_password(
            "authentication-timing-placeholder"
        )

    def register(
        self,
        *,
        email: str,
        username: str,
        password: str,
    ) -> User:
        users = self._users.list_all()
        self._ensure_identity_available(
            users,
            email=email,
            username=username,
        )

        now = datetime.now(timezone.utc)
        user = User(
            user_id=str(uuid4()),
            recent_movie_ids=[],
            schema_version=2,
            onboarding_genres=None,
            user_settings=UserSettings(
                email=email.casefold(),
                username=username,
                password_hash=self._password_hasher.hash_password(password),
                created_at=now,
            ),
        )
        return self._users.create(user)

    def authenticate(self, *, identity: str, password: str) -> User:
        user = self._find_by_identity(identity)
        encoded_hash = (
            user.password_hash
            if user is not None
            and self._password_hasher.is_supported_hash(user.password_hash)
            else self._dummy_password_hash
        )
        try:
            valid_password = self._password_hasher.verify_password(
                password,
                encoded_hash,
            )
        except PasswordHashError:
            valid_password = False

        if user is not None and not valid_password:
            valid_password = self._verify_legacy_dev_password(user, password)

        if user is None or not valid_password:
            raise InvalidCredentialsError("Invalid credentials")

        # Login is intentionally read-only because the deployed Users schema
        # has no last_active_at field and must not be rewritten during auth.
        return user

    def get_user(self, user_id: str) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError("Authenticated user no longer exists")
        return user

    def update_profile(
        self,
        *,
        user_id: str,
        email: str | None,
        username: str | None,
    ) -> User:
        user = self.get_user(user_id)
        users = self._users.list_all()
        next_email = email.casefold() if email is not None else user.email
        next_username = username if username is not None else user.username
        self._ensure_identity_available(
            users,
            email=next_email,
            username=next_username,
            exclude_user_id=user_id,
        )

        settings = user.user_settings.model_copy(
            update={
                "email": next_email,
                "username": next_username,
            }
        )
        updated = user.model_copy(update={"user_settings": settings})
        return self._users.update(updated)

    def complete_onboarding(
        self,
        *,
        user_id: str,
        onboarding_genres: list[str],
    ) -> User:
        user = self.get_user(user_id)
        updated = user.model_copy(
            update={
                "onboarding_genres": onboarding_genres,
            }
        )
        return self._users.update(updated)

    def _verify_legacy_dev_password(self, user: User, password: str) -> bool:
        """Allow only the deterministic schema-v2 seed credential shape."""

        if not self._allow_legacy_dev_login or user.schema_version != 2:
            return False

        expected_username = f"{user.user_id}#username"
        expected_email = f"{user.user_id}@email.com"
        expected_password = f"{user.user_id}#pass"
        return (
            hmac.compare_digest(user.username, expected_username)
            and hmac.compare_digest(user.email.casefold(), expected_email.casefold())
            and hmac.compare_digest(user.password_hash, expected_password)
            and hmac.compare_digest(password, expected_password)
        )

    def _find_by_identity(self, identity: str) -> User | None:
        normalized = identity.casefold()
        seed_user_id = self._seed_user_id_from_identity(normalized)
        if seed_user_id is not None:
            seed_user = self._users.get(seed_user_id)
            if seed_user is not None and (
                seed_user.username.casefold() == normalized
                or seed_user.email.casefold() == normalized
            ):
                return seed_user

        return next(
            (
                user
                for user in self._users.list_all()
                if user.username.casefold() == normalized
                or user.email.casefold() == normalized
            ),
            None,
        )

    @staticmethod
    def _seed_user_id_from_identity(identity: str) -> str | None:
        """Resolve deterministic seed identities without scanning Users."""

        for suffix in ("#username", "@email.com"):
            if identity.endswith(suffix):
                user_id = identity[: -len(suffix)]
                return user_id or None
        return None

    @staticmethod
    def _ensure_identity_available(
        users: list[User],
        *,
        email: str,
        username: str,
        exclude_user_id: str | None = None,
    ) -> None:
        normalized_email = email.casefold()
        normalized_username = username.casefold()
        for user in users:
            if user.user_id == exclude_user_id:
                continue
            if user.email.casefold() == normalized_email:
                raise AccountConflictError("Email is already registered")
            if user.username.casefold() == normalized_username:
                raise AccountConflictError("Username is already registered")
