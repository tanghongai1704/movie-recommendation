import os
from pathlib import Path


def _required_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Required environment variable is not set: {name}")
    return value


class Settings:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    API_V1_PREFIX = "/api/v1"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    AUTH_TOKEN_PREFIX = os.getenv("AUTH_TOKEN_PREFIX", "dummy-token-for-")
    AWS_REGION = _required_environment_variable("AWS_REGION")
    AWS_DYNAMODB_TABLE_MOVIES = _required_environment_variable(
        "AWS_DYNAMODB_TABLE_MOVIES"
    )
    AWS_DYNAMODB_TABLE_POPULAR = _required_environment_variable(
        "AWS_DYNAMODB_TABLE_POPULAR"
    )
    AWS_DYNAMODB_TABLE_USERS = _required_environment_variable(
        "AWS_DYNAMODB_TABLE_USERS"
    )
    AWS_DYNAMODB_TABLE_INTERACTIONS = _required_environment_variable(
        "AWS_DYNAMODB_TABLE_INTERACTIONS"
    )
    AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE = _required_environment_variable(
        "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE"
    )
    RECOMMENDATION_CACHE_TTL_SECONDS = int(
        os.getenv("RECOMMENDATION_CACHE_TTL_SECONDS", "300")
    )


settings = Settings()
