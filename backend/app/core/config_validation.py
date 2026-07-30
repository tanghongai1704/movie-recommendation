"""Reusable environment and startup configuration validation."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from urllib.parse import urlparse


class ConfigurationError(RuntimeError):
    """Raised when runtime configuration is missing or inconsistent."""


def environment_value(
    name: str,
    *,
    aliases: Iterable[str] = (),
    default: str | None = None,
    required: bool = False,
) -> str | None:
    """Read one setting, accepting temporary legacy aliases.

    A conflicting primary and legacy value fails fast instead of silently
    connecting the application to an unexpected AWS resource.
    """

    names = (name, *tuple(aliases))
    configured = {
        candidate: value.strip()
        for candidate in names
        if (value := os.getenv(candidate)) is not None and value.strip()
    }
    if len(set(configured.values())) > 1:
        joined = ", ".join(configured)
        raise ConfigurationError(
            f"Conflicting environment variables are set for {name}: {joined}"
        )
    if configured:
        return configured.get(name) or next(iter(configured.values()))
    if default is not None:
        return default
    if required:
        alias_text = (
            f" (legacy aliases: {', '.join(names[1:])})"
            if len(names) > 1
            else ""
        )
        raise ConfigurationError(
            f"Required environment variable is not set: {name}{alias_text}"
        )
    return None


def boolean_value(
    name: str,
    *,
    aliases: Iterable[str] = (),
    default: bool,
) -> bool:
    raw = environment_value(
        name,
        aliases=aliases,
        default="true" if default else "false",
    )
    normalized = str(raw).lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(
        f"{name} must be one of true, false, 1, 0, yes, no, on, or off"
    )


def integer_value(
    name: str,
    *,
    aliases: Iterable[str] = (),
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
    required: bool = False,
) -> int:
    raw = environment_value(
        name,
        aliases=aliases,
        default=str(default) if default is not None else None,
        required=required,
    )
    try:
        value = int(str(raw))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if minimum is not None and value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigurationError(f"{name} must be at most {maximum}")
    return value


def csv_value(
    name: str,
    *,
    default: str | None = None,
    required: bool = False,
) -> tuple[str, ...]:
    raw = environment_value(name, default=default, required=required)
    values = tuple(part.strip() for part in str(raw or "").split(",") if part.strip())
    if required and not values:
        raise ConfigurationError(f"{name} must contain at least one value")
    return values


def validate_http_url(
    value: str | None,
    *,
    name: str,
    required: bool = False,
) -> str | None:
    if value is None or not value.strip():
        if required:
            raise ConfigurationError(f"{name} must be a non-empty HTTP(S) URL")
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError(f"{name} must be a valid HTTP(S) URL")
    return value.rstrip("/")


def validate_cors_origins(values: tuple[str, ...]) -> tuple[str, ...]:
    if "*" in values:
        if len(values) != 1:
            raise ConfigurationError(
                "CORS_ALLOWED_ORIGINS cannot combine '*' with explicit origins"
            )
        return values
    return tuple(
        str(
            validate_http_url(
                value,
                name="CORS_ALLOWED_ORIGINS",
                required=True,
            )
        )
        for value in values
    )


def validate_api_path(value: str, *, name: str) -> str:
    if not value.startswith("/"):
        raise ConfigurationError(f"{name} must start with '/'")
    if len(value) > 1 and value.endswith("/"):
        raise ConfigurationError(f"{name} must not end with '/'")
    if "://" in value or any(character.isspace() for character in value):
        raise ConfigurationError(f"{name} must be an absolute URL path")
    return value


def validate_log_level(value: str) -> str:
    normalized = value.upper()
    if normalized not in {
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG",
        "NOTSET",
    }:
        raise ConfigurationError(
            "LOG_LEVEL must be CRITICAL, ERROR, WARNING, INFO, DEBUG, or NOTSET"
        )
    return normalized


def validate_jwt_secret(value: str) -> str:
    if len(value.encode("utf-8")) < 32:
        raise ConfigurationError(
            "JWT_SECRET_KEY must contain at least 32 bytes"
        )
    return value


def validate_jwt_algorithm(value: str) -> str:
    normalized = value.upper()
    if normalized != "HS256":
        raise ConfigurationError(
            "JWT_ALGORITHM must be HS256; no other algorithm is implemented"
        )
    return normalized


def validate_aws_region(value: str) -> str:
    if not re.fullmatch(r"[a-z]{2}(?:-gov)?-[a-z]+-\d", value):
        raise ConfigurationError(
            "AWS_REGION must be a valid AWS region identifier"
        )
    return value


def validate_s3_bucket_name(value: str) -> str:
    if not 3 <= len(value) <= 63:
        raise ConfigurationError(
            "AWS_S3_BUCKET must contain between 3 and 63 characters"
        )
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", value):
        raise ConfigurationError(
            "AWS_S3_BUCKET must use a valid lowercase S3 bucket name"
        )
    if ".." in value or ".-" in value or "-." in value:
        raise ConfigurationError("AWS_S3_BUCKET contains an invalid label")
    return value


def validate_s3_prefix(
    value: str | None,
    *,
    name: str,
    required: bool = False,
) -> str | None:
    if value is None or not value.strip():
        if required:
            raise ConfigurationError(
                f"Required environment variable is not set: {name}"
            )
        return None
    normalized = value.strip().lstrip("/")
    if normalized in {".", ".."} or "/../" in f"/{normalized}/":
        raise ConfigurationError(f"{name} must not contain parent path segments")
    return normalized.rstrip("/") + "/"


def validate_sagemaker_resource_name(
    value: str | None,
    *,
    name: str,
    required: bool = False,
) -> str | None:
    if value is None or not value.strip():
        if required:
            raise ConfigurationError(
                f"Required environment variable is not set: {name}"
            )
        return None
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", value):
        raise ConfigurationError(
            f"{name} must be a valid SageMaker resource name"
        )
    return value


def validate_aws_credentials(*, enabled: bool) -> None:
    """Fail fast when neither explicit nor default-chain credentials exist."""

    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    session_token = os.getenv("AWS_SESSION_TOKEN", "").strip()
    if bool(access_key) != bool(secret_key):
        raise ConfigurationError(
            "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set together"
        )
    if session_token and not access_key:
        raise ConfigurationError(
            "AWS_SESSION_TOKEN requires AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY"
        )
    if not enabled or (access_key and secret_key):
        return

    try:
        import boto3

        credentials = boto3.Session().get_credentials()
    except Exception as exc:
        raise ConfigurationError(
            "Unable to inspect the AWS default credential provider chain"
        ) from exc
    if credentials is None:
        raise ConfigurationError(
            "AWS credentials are unavailable. Use an IAM role, workload "
            "identity, AWS SSO/AWS_PROFILE, or explicit local credentials."
        )
