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
    JWT_SECRET = _required_environment_variable("JWT_SECRET")
    JWT_ISSUER = os.getenv("JWT_ISSUER", "movie-recommendation-api")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "movie-recommendation-frontend")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    PASSWORD_HASH_ITERATIONS = int(
        os.getenv("PASSWORD_HASH_ITERATIONS", "10000")
    )
    ALLOW_LEGACY_DEV_LOGIN = (
        os.getenv("ALLOW_LEGACY_DEV_LOGIN", "False").lower() == "true"
    )
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
