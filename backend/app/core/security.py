from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


class PasswordHashError(ValueError):
    """Raised when a stored password hash does not use the supported format."""


class TokenValidationError(ValueError):
    """Raised when a JWT is malformed, invalid, or expired."""


class PasswordHasher:
    """PBKDF2-HMAC-SHA256 password hashing with a unique random salt."""

    algorithm = "pbkdf2_hmac_sha256"
    supported_algorithms = frozenset(
        {
            algorithm,
            "pbkdf2_sha256",
        }
    )

    def __init__(self, *, iterations: int = 10_000) -> None:
        if iterations < 10_000:
            raise ValueError("password hash iterations must be at least 10000")
        self._iterations = iterations

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("password must not be empty")

        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._iterations,
            dklen=32,
        )
        return "$".join(
            (
                self.algorithm,
                str(self._iterations),
                self._encode(salt),
                self._encode(digest),
            )
        )

    def verify_password(self, password: str, encoded_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, digest_text = encoded_hash.split(
                "$",
                maxsplit=3,
            )
            if algorithm not in self.supported_algorithms:
                raise PasswordHashError("unsupported password hash algorithm")

            iterations = int(iterations_text)
            if iterations < 10_000 or iterations > 2_000_000:
                raise PasswordHashError("invalid password hash iteration count")

            salt = self._decode(salt_text)
            expected_digest = self._decode(digest_text)
        except (TypeError, ValueError, binascii.Error) as exc:
            if isinstance(exc, PasswordHashError):
                raise
            raise PasswordHashError("invalid password hash format") from exc

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected_digest),
        )
        return hmac.compare_digest(actual_digest, expected_digest)

    @classmethod
    def is_supported_hash(cls, encoded_hash: str) -> bool:
        """Return whether a value declares one of the supported PBKDF2 tags."""

        algorithm, separator, _ = encoded_hash.partition("$")
        return separator == "$" and algorithm in cls.supported_algorithms

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)


@dataclass(frozen=True)
class TokenClaims:
    """Validated access-token claims attached to the current request."""

    user_id: str
    token_id: str
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class IssuedAccessToken:
    """Encoded access token and its lifetime in seconds."""

    token: str
    expires_in: int


class JWTService:
    """Minimal HS256 JWT issuer and validator for access tokens."""

    def __init__(
        self,
        *,
        secret: str,
        algorithm: str = "HS256",
        issuer: str,
        audience: str,
        access_token_minutes: int,
    ) -> None:
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")
        if algorithm != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")
        if not issuer or not audience:
            raise ValueError("JWT issuer and audience must not be empty")
        if access_token_minutes <= 0:
            raise ValueError("JWT access token lifetime must be positive")

        self._secret = secret.encode("utf-8")
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience
        self._lifetime = timedelta(minutes=access_token_minutes)

    def issue_access_token(self, user_id: str) -> IssuedAccessToken:
        if not user_id:
            raise ValueError("user_id must not be empty")

        now = datetime.now(timezone.utc)
        expires_at = now + self._lifetime
        payload = {
            "sub": user_id,
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
            "token_type": "access",
        }
        header = {"alg": self._algorithm, "typ": "JWT"}
        encoded_header = self._encode_json(header)
        encoded_payload = self._encode_json(payload)
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        signature = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        token = f"{encoded_header}.{encoded_payload}.{self._encode_bytes(signature)}"
        return IssuedAccessToken(
            token=token,
            expires_in=int(self._lifetime.total_seconds()),
        )

    def decode_access_token(self, token: str) -> TokenClaims:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            header = self._decode_json(encoded_header)
            payload = self._decode_json(encoded_payload)
            signature = self._decode_bytes(encoded_signature)
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
            binascii.Error,
            UnicodeDecodeError,
        ) as exc:
            raise TokenValidationError("invalid access token") from exc

        if (
            header.get("alg") != self._algorithm
            or header.get("typ") != "JWT"
        ):
            raise TokenValidationError("invalid access token")

        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(
            self._secret,
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise TokenValidationError("invalid access token")

        try:
            user_id = str(payload["sub"])
            token_id = str(payload["jti"])
            issued_at_seconds = int(payload["iat"])
            expires_at_seconds = int(payload["exp"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TokenValidationError("invalid access token") from exc

        now_seconds = int(datetime.now(timezone.utc).timestamp())
        if expires_at_seconds <= now_seconds:
            raise TokenValidationError("access token has expired")
        if issued_at_seconds > now_seconds + 30:
            raise TokenValidationError("invalid access token")
        if payload.get("iss") != self._issuer:
            raise TokenValidationError("invalid access token")
        if payload.get("aud") != self._audience:
            raise TokenValidationError("invalid access token")
        if payload.get("token_type") != "access" or not user_id or not token_id:
            raise TokenValidationError("invalid access token")

        return TokenClaims(
            user_id=user_id,
            token_id=token_id,
            issued_at=datetime.fromtimestamp(issued_at_seconds, tz=timezone.utc),
            expires_at=datetime.fromtimestamp(expires_at_seconds, tz=timezone.utc),
        )

    @classmethod
    def _encode_json(cls, value: dict[str, Any]) -> str:
        serialized = json.dumps(
            value,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return cls._encode_bytes(serialized)

    @classmethod
    def _decode_json(cls, value: str) -> dict[str, Any]:
        decoded = json.loads(cls._decode_bytes(value))
        if not isinstance(decoded, dict):
            raise TokenValidationError("invalid access token")
        return decoded

    @staticmethod
    def _encode_bytes(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode_bytes(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)
